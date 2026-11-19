"""Integration tests for CPU player move application."""

import copy
import os

import pytest
from bson.objectid import ObjectId
from fastapi import HTTPException, Response

import src.api as api
import src.cpu_player as cpu_player
from src.database import mongo_client
from src.cpu_player import (
    get_all_valid_moves,
    apply_cpu_move,
    process_game,
    get_marked_for_death_moves,
)
from src.utils.game_state import clear_game
from tests.test_utils import select_and_move_white_piece


def test_cpu_makes_valid_move_on_starting_position(game):
    """After white's first move, CPU should be able to make a valid black move."""
    # White moves pawn from [6, 4] to [4, 4] (e4)
    game = select_and_move_white_piece(game, 6, 4, 4, 4)
    assert game["turn_count"] == 1  # Now it's black's turn

    # Generate valid moves for black
    valid_moves = get_all_valid_moves(game)
    assert len(valid_moves) > 0

    # Apply a random valid move
    chosen_move = valid_moves[0]
    result = apply_cpu_move(game["id"], game, chosen_move)

    # Turn should have advanced (now white's turn again)
    assert result["turn_count"] % 2 == 0


def test_cpu_capture_move(game):
    """CPU should be able to capture a white piece."""
    game = clear_game(game)

    # Set up: white pawn at [4, 4], black pawn at [3, 3]
    game_state = copy.deepcopy(game)
    game_state["board_state"][4][4] = [{"type": "white_pawn", "pawn_buff": 0}]
    game_state["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0}]
    game_state["board_state"][0][4] = [{"type": "black_king"}]
    game_state["board_state"][7][4] = [{"type": "white_king"}]
    game_state["turn_count"] = 1

    request = api.GameStateRequest(**game_state)
    game = api.update_game_state_no_restrictions(game["id"], request, Response())

    valid_moves = get_all_valid_moves(game)

    capture_moves = [m for m in valid_moves if m["type"] == "capture" and m["from_pos"] == [3, 3]]
    assert len(capture_moves) > 0

    capture_move = capture_moves[0]
    result = apply_cpu_move(game["id"], game, capture_move)

    # Verify capture was recorded
    assert "white_pawn" in result["captured_pieces"]["black"]
    assert result["turn_count"] % 2 == 0


def test_cpu_handles_no_valid_moves_gracefully(game):
    """CPU should handle stalemate/no-move situations without crashing."""
    game = clear_game(game)

    # Set up a position with no valid black moves (stalemate-like)
    # Black king boxed in with no legal moves
    game_state = copy.deepcopy(game)
    game_state["board_state"][0][0] = [{"type": "black_king"}]
    game_state["board_state"][7][7] = [{"type": "white_king"}]
    game_state["board_state"][1][7] = [{"type": "white_rook"}]
    game_state["board_state"][7][1] = [{"type": "white_rook"}]
    game_state["board_state"][2][2] = [{"type": "white_queen"}]
    game_state["turn_count"] = 1

    request = api.GameStateRequest(**game_state)
    game = api.update_game_state_no_restrictions(game["id"], request, Response())

    valid_moves = get_all_valid_moves(game)
    # May have 0 moves if truly stalemated — should not crash
    # (exact count depends on the specific position)


def test_cpu_castle_move(game):
    """CPU should be able to castle when conditions are met."""
    game = clear_game(game)

    game_state = copy.deepcopy(game)
    game_state["board_state"][0][4] = [{"type": "black_king"}]
    game_state["board_state"][0][7] = [{"type": "black_rook"}]
    game_state["board_state"][7][4] = [{"type": "white_king"}]
    game_state["turn_count"] = 1
    game_state["castle_log"] = {
        "white": {"has_king_moved": False, "has_left_rook_moved": False, "has_right_rook_moved": False},
        "black": {"has_king_moved": False, "has_left_rook_moved": False, "has_right_rook_moved": False},
    }

    request = api.GameStateRequest(**game_state)
    game = api.update_game_state_no_restrictions(game["id"], request, Response())

    valid_moves = get_all_valid_moves(game)
    castle_moves = [m for m in valid_moves if m["type"] == "castle"]
    assert len(castle_moves) > 0

    castle_move = castle_moves[0]
    result = apply_cpu_move(game["id"], game, castle_move)

    # King should have moved to castle destination
    king_dest = castle_move["to_pos"]
    king_square = result["board_state"][king_dest[0]][king_dest[1]]
    assert any("black_king" == p["type"] for p in king_square)
    assert result["turn_count"] % 2 == 0


# ---------------------------------------------------------------------------
# Difficulty
# ---------------------------------------------------------------------------

def _delete_game(game_id):
    game_database = mongo_client["game_db"]
    game_database["games"].delete_one({"_id": ObjectId(game_id)})
    game_database["game_moves"].delete_many({"game_id": game_id})
    game_database["game_state_history"].delete_many({"game_id": game_id})


@pytest.fixture
def hard_game():
    game = api.create_game(api.CreateGameRequest(cpu_difficulty="hard"))
    yield game
    _delete_game(game["id"])


def test_create_game_defaults_to_easy(game):
    assert game["cpu_difficulty"] == "easy"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_create_game_stores_requested_difficulty(difficulty):
    game = api.create_game(api.CreateGameRequest(cpu_difficulty=difficulty))
    try:
        assert game["cpu_difficulty"] == difficulty
        assert api.retrieve_game_state(game["id"], Response())["cpu_difficulty"] == difficulty
    finally:
        _delete_game(game["id"])


def test_create_game_rejects_unknown_difficulty():
    with pytest.raises(HTTPException) as exc_info:
        api.create_game(api.CreateGameRequest(cpu_difficulty="impossible"))
    assert exc_info.value.status_code == 400


def test_client_cannot_change_difficulty_mid_game(hard_game):
    tampered = copy.deepcopy(hard_game)
    tampered["cpu_difficulty"] = "easy"
    tampered["position_in_play"] = [6, 4]

    result = api.update_game_state(hard_game["id"], api.GameStateRequest(**tampered), Response())

    assert result["cpu_difficulty"] == "hard"


def test_hard_cpu_completes_a_move(hard_game, monkeypatch):
    """process_game on a hard game searches and plays a legal black move."""
    monkeypatch.setattr(cpu_player, "HARD_THINK_SECONDS", 0.5)
    monkeypatch.setattr(cpu_player, "CPU_MOVE_DELAY_SECONDS", 0)
    game = select_and_move_white_piece(hard_game, 6, 4, 4, 4)
    assert game["turn_count"] == 1

    process_game(game["id"], "test-instance")

    result = api.retrieve_game_state(game["id"], Response())
    assert result["turn_count"] == 2
    assert result["cpu_difficulty"] == "hard"
    assert result["latest_movement"]["record"][0]["side"] == "black"


def test_hard_cpu_takes_hanging_queen(hard_game, monkeypatch):
    monkeypatch.setattr(cpu_player, "HARD_THINK_SECONDS", 1.0)
    monkeypatch.setattr(cpu_player, "CPU_MOVE_DELAY_SECONDS", 0)
    game = clear_game(hard_game)
    game_state = copy.deepcopy(game)
    # clear_game resets every field to the empty mock, including the difficulty
    game_state["cpu_difficulty"] = "hard"
    game_state["board_state"][0][4] = [{"type": "black_king"}]
    game_state["board_state"][7][4] = [{"type": "white_king"}]
    game_state["board_state"][2][2] = [{"type": "black_knight"}]
    game_state["board_state"][4][1] = [{"type": "white_queen"}]
    game_state["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    game_state["turn_count"] = 1
    api.update_game_state_no_restrictions(game["id"], api.GameStateRequest(**game_state), Response())

    process_game(game["id"], "test-instance")

    result = api.retrieve_game_state(game["id"], Response())
    assert "white_queen" in result["captured_pieces"]["black"]


@pytest.mark.parametrize("difficulty", ["easy", "hard"])
def test_cpu_resolves_full_bishop_debuff_instead_of_stalling(difficulty, monkeypatch):
    """With a white piece at 3 bishop debuff stacks, the CPU must capture or spare it."""
    monkeypatch.setattr(cpu_player, "CPU_MOVE_DELAY_SECONDS", 0)
    game = api.create_game(api.CreateGameRequest(cpu_difficulty=difficulty))
    try:
        game = clear_game(game)
        game_state = copy.deepcopy(game)
        # clear_game resets every field to the empty mock, including the difficulty
        game_state["cpu_difficulty"] = difficulty
        game_state["board_state"][0][4] = [{"type": "black_king"}]
        game_state["board_state"][7][4] = [{"type": "white_king"}]
        game_state["board_state"][1][1] = [{"type": "black_bishop", "energize_stacks": 0}]
        game_state["board_state"][5][5] = [{"type": "white_knight", "bishop_debuff": 2}]
        game_state["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
        game_state["turn_count"] = 1
        game = api.update_game_state_no_restrictions(game["id"], api.GameStateRequest(**game_state), Response())

        # Black bishop moves so the knight is on its diagonal, giving the third stack
        after_move = apply_cpu_move(game["id"], game, {"type": "move", "from_pos": [1, 1], "to_pos": [2, 2]})
        assert after_move["board_state"][5][5][0]["bishop_debuff"] == 3
        assert after_move["turn_count"] == 1

        process_game(game["id"], "test-instance")

        result = api.retrieve_game_state(game["id"], Response())
        assert result["turn_count"] == 2
        knight_square = result["board_state"][5][5]
        if difficulty == "hard":
            assert knight_square is None
            assert "white_knight" in result["captured_pieces"]["black"]
        else:
            assert knight_square is None or knight_square[0].get("bishop_debuff", 0) == 0
    finally:
        _delete_game(game["id"])
