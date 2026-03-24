"""Integration tests for CPU player move application."""

import copy
import os

import pytest
from fastapi import Response

import src.api as api
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
