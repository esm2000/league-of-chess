"""Integration tests for the replay endpoint and state history snapshots."""

import copy

from fastapi import Response

import src.api as api
from src.database import mongo_client
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_white_piece,
    move_white_piece,
    select_black_piece,
    move_black_piece,
    select_and_move_white_piece,
    select_and_move_black_piece,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_replay(game_id):
    """Call the replay endpoint and return the list of states."""
    return api.get_game_replay(game_id, Response())


def get_snapshot_count(game_id):
    """Count snapshots in game_state_history for a game."""
    return mongo_client["game_db"]["game_state_history"].count_documents({"game_id": game_id})


def setup_custom_board(game, pieces, turn_count=0, extra=None):
    """Clear the board and place specific pieces. Returns the updated game.

    pieces: list of (row, col, piece_dict) tuples
    extra: dict of additional game state overrides
    """
    game = clear_game(game)
    game_setup = copy.deepcopy(game)
    for row, col, piece in pieces:
        game_setup["board_state"][row][col] = [piece] if isinstance(piece, dict) else piece
    game_setup["turn_count"] = turn_count
    if extra:
        for key, value in extra.items():
            game_setup[key] = value
    game_setup["previous_state"] = copy.deepcopy(game_setup)
    return api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**game_setup), Response()
    )


def perform_capture(game, from_row, from_col, to_row, to_col, captured_type, side="white"):
    """Select a piece and perform a capture move."""
    if side == "white":
        game = select_white_piece(game, from_row, from_col)
    else:
        game = select_black_piece(game, from_row, from_col)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][to_row][to_col] = game_on_next_turn["board_state"][from_row][from_col]
    game_on_next_turn["board_state"][from_row][from_col] = None
    game_on_next_turn["captured_pieces"][side].append(captured_type)
    game_state = api.GameStateRequest(**game_on_next_turn)
    if side == "white":
        game = api.update_game_state(game["id"], game_state, Response())
    else:
        game = api.update_game_state(game["id"], game_state, Response(), player=False)
    return game


# ---------------------------------------------------------------------------
# Basic movement tests
# ---------------------------------------------------------------------------

def test_empty_replay(game):
    """New game with no moves → replay returns empty list."""
    result = get_replay(game["id"])
    assert result == []


def test_single_turn_replay(game):
    """Single white turn (select + move) → replay shows only that one turn.

    cpu_id is set to prevent the CPU from claiming and playing black's turn.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (6, 4, {"type": "white_pawn", "pawn_buff": 0}),
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        },
        "cpu_id": "disabled"
    })

    game = select_and_move_white_piece(game, 6, 4, 4, 4)  # e2→e4

    result = get_replay(game["id"])
    assert len(result) >= 2

    # Should only contain turn 0 (select) and turn 1 (after move)
    assert result[0]["turn_count"] == 0
    assert result[-1]["turn_count"] == 1


def test_basic_two_turn_replay(game):
    """White moves, black moves → replay covers both turns."""
    game = select_and_move_white_piece(game, 6, 0, 5, 0)  # a2→a3
    game = select_and_move_black_piece(game, 1, 0, 2, 0)  # a7→a6

    result = get_replay(game["id"])
    assert len(result) >= 4  # at least select+move for each side

    turn_counts = [s["turn_count"] for s in result]
    assert len(set(turn_counts)) >= 2


def test_castle_replay(game):
    """Castling move → replay shows king selection with castle button, then castle executed.

    Note: The 'Castle Right' button appears in all frames where castling is legal
    (not just when the king is selected). This is expected frontend behavior.
    """
    # Clear path for kingside castle: remove knight and bishop
    game_setup = copy.deepcopy(game)
    game_setup["board_state"][7][5] = None
    game_setup["board_state"][7][6] = None
    game_setup["previous_state"] = copy.deepcopy(game_setup)
    game = api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**game_setup), Response()
    )

    # White pawn move + black response to build history
    game = select_and_move_white_piece(game, 6, 4, 4, 4)  # e2→e4
    game = select_and_move_black_piece(game, 1, 0, 2, 0)  # a7→a6

    # White: select king then castle kingside
    game = select_white_piece(game, 7, 4)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][7][6] = game_on_next_turn["board_state"][7][4]
    game_on_next_turn["board_state"][7][4] = None
    game_on_next_turn["board_state"][7][5] = game_on_next_turn["board_state"][7][7]
    game_on_next_turn["board_state"][7][7] = None
    game = api.update_game_state(
        game["id"], api.GameStateRequest(**game_on_next_turn), Response()
    )

    result = get_replay(game["id"])
    assert len(result) >= 2

    last = result[-1]
    king_square = last["board_state"][7][6]
    assert king_square is not None
    assert any(p["type"] == "white_king" for p in king_square)


# ---------------------------------------------------------------------------
# Capture tests
# ---------------------------------------------------------------------------

def test_standard_capture_replay(game):
    """White pawn captures black pawn → replay includes capture state."""
    # d2→d4, e7→e5, then white d4 captures e5
    game = select_and_move_white_piece(game, 6, 3, 4, 3)
    game = select_and_move_black_piece(game, 1, 4, 3, 4)
    game = perform_capture(game, 4, 3, 3, 4, "black_pawn", "white")

    result = get_replay(game["id"])
    assert len(result) >= 2
    has_capture = any(
        "black_pawn" in s.get("captured_pieces", {}).get("white", [])
        for s in result
    )
    assert has_capture


def test_capture_to_escape_check_replay(game):
    """White checks black with bishop → black captures bishop to escape.

    Replay shows: white bishop delivers check → black captures bishop → check resolved.
    """
    # White bishop at d7=[1,3] one diagonal step from checking king at e8=[0,4]
    # Bishop moves to c6=[2,2]? No — need bishop to land on square that attacks king.
    # Bishop at d7=[1,3] already adjacent diagonally to king at e8=[0,4]. Place it further.
    # Bishop at c6=[2,2] → d7=[1,3] checks king at e8=[0,4] (1 step diagonal)
    # Black knight at e6=[2,4] can jump to d4 — no, need to capture the bishop at d7=[1,3]
    # Knight at e6=[2,4] can jump to d4,f4,c5,g5,c7,g7 — can't reach d7
    # Knight at c8=[0,2] can jump to b6=[2,1] or a7=[1,0] or d6=[2,3] or e7=[1,4] — can't reach d7
    # Use a black rook instead — rook at d8=[0,3] can capture d7=[1,3]
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (2, 2, {"type": "white_bishop", "energize_stacks": 0}),  # c6
        (0, 4, {"type": "black_king"}),  # e8
        (0, 3, {"type": "black_rook"}),  # d8 — can capture bishop at d7
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White bishop c6=[2,2] → d7=[1,3] (1 diagonal step, checks king at e8=[0,4])
    game = select_and_move_white_piece(game, 2, 2, 1, 3)
    assert game["check"]["black"] == True

    # Black rook d8=[0,3] captures bishop at d7=[1,3]
    game = perform_capture(game, 0, 3, 1, 3, "white_bishop", "black")
    assert game["check"]["black"] == False

    result = get_replay(game["id"])
    assert len(result) >= 2
    has_check = any(s.get("check", {}).get("black", False) for s in result)
    assert has_check


# ---------------------------------------------------------------------------
# Check scenarios
# ---------------------------------------------------------------------------

def test_check_replay(game):
    """White delivers check → black responds → replay shows check and response."""
    # White rook on e-file checks black king on e8
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (7, 0, {"type": "white_rook"}),  # a1 — will move to e1 then up
        (6, 4, {"type": "white_pawn", "pawn_buff": 0}),  # e2 blocker
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (1, 3, {"type": "black_pawn", "pawn_buff": 0}),  # d7
    ], turn_count=0)

    # Simpler: place rook where it can move to check directly
    game = setup_custom_board(game, [
        (7, 3, {"type": "white_king"}),  # d1 (off e-file)
        (4, 4, {"type": "white_rook"}),  # e4 — can move to e8 file to check
        (0, 4, {"type": "black_king"}),  # e8
        (0, 0, {"type": "black_rook"}),
        (1, 3, {"type": "black_pawn", "pawn_buff": 0}),  # d7 — can block on e file? No.
        (1, 5, {"type": "black_pawn", "pawn_buff": 0}),  # f7
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": False, "has_left_rook_moved": False, "has_right_rook_moved": False}
        }
    })

    # White rook e4→e7 — one square away from king, checks along file? No, e7=[1,4]
    # Rook at e4=[4,4], king at e8=[0,4]. Path: e5,e6,e7 are empty. Rook can go to e7=[1,4]?
    # Wait, rows go 0=8th rank, 7=1st rank. So e4=[4,4] and e8=[0,4].
    # Rook can move from [4,4] to [1,4] (e7) — that's adjacent to king at [0,4].
    # Or [2,4] (e6), [3,4] (e5). Let's go to [1,4] to be right next to king.
    # Actually for check we need the rook to attack the king square.
    # Rook at [1,4] attacks [0,4] (king). That's check!
    game = select_and_move_white_piece(game, 4, 4, 1, 4)  # Re4→e7 (attacks e8)

    assert game["check"]["black"] == True

    # Black king moves to escape — king at e8=[0,4], can go to d8=[0,3] or f8=[0,5]
    game = select_and_move_black_piece(game, 0, 4, 0, 3)  # Ke8→d8

    result = get_replay(game["id"])
    assert len(result) >= 2
    has_check = any(s.get("check", {}).get("black", False) for s in result)
    assert has_check
    # Last state should have check resolved
    assert result[-1]["check"]["black"] == False


def test_check_escape_by_blocking_replay(game):
    """White bishop checks black → black rook blocks diagonal → check resolved.

    Bishop check along diagonal, black interposes rook on the diagonal to block.
    """
    # Bishop at f2=[6,5] NOT on diagonal to a7, so black starts NOT in check.
    # Bishop moves to d4=[4,3] which checks king at a7=[1,0] via diagonal d4-c5-b6-a7.
    # Black rook at c8=[0,2] interposes at c5=[3,2] to block.
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (6, 5, {"type": "white_bishop", "energize_stacks": 0}),  # f2 — not checking a7
        (1, 0, {"type": "black_king"}),  # a7
        (0, 2, {"type": "black_rook"}),  # c8 — can move to c5=[3,2] to block
        (1, 1, {"type": "black_pawn", "pawn_buff": 0}),
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    assert game["check"]["black"] == False  # not in check initially

    # White bishop f2=[6,5] → d4=[4,3] — checks king at a7=[1,0] via diagonal d4-c5-b6-a7
    game = select_and_move_white_piece(game, 6, 5, 4, 3)
    assert game["check"]["black"] == True

    # Black rook c8=[0,2] → c5=[3,2] — blocks the diagonal between d4 and a7
    game = select_and_move_black_piece(game, 0, 2, 3, 2)
    assert game["check"]["black"] == False

    result = get_replay(game["id"])
    assert len(result) >= 2
    has_check = any(s.get("check", {}).get("black", False) for s in result)
    assert has_check
    assert result[-1]["check"]["black"] == False


# ---------------------------------------------------------------------------
# Turn extension tests
# ---------------------------------------------------------------------------

def test_queen_reset_replay(game):
    """Queen captures → gets extra turn → makes second move.

    Replay shows: queen selects → queen captures pawn → queen re-selects (reset) → queen moves again.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (7, 3, {"type": "white_queen"}),  # d1
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (3, 3, {"type": "black_pawn", "pawn_buff": 0}),  # d5 — queen can capture
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White queen captures d5 pawn: d1→d5
    game = perform_capture(game, 7, 3, 3, 3, "black_pawn", "white")

    # Queen should have reset (queen_reset=True or turn didn't increment)
    # The queen gets to move again at the same turn_count
    assert game["queen_reset"] == True or game["turn_count"] == 0

    # Queen makes second move: d5→d7 (threatening)
    game = select_and_move_white_piece(game, 3, 3, 1, 3)  # Qd5→d7

    result = get_replay(game["id"])
    assert len(result) >= 3  # select, capture, reset move

    # Should have multiple states at same turn_count (queen reset)
    turn_counts = [s["turn_count"] for s in result]
    # The capture and reset move should share a turn_count
    assert len(turn_counts) > len(set(turn_counts))  # duplicates exist


def test_pawn_exchange_replay(game):
    """Pawn promotes → exchange to queen → black responds.

    Replay shows: pawn to rank 0 → exchange to queen → black makes a move.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (1, 0, {"type": "white_pawn", "pawn_buff": 0}),  # a7 — one step from promotion
        (2, 4, {"type": "black_king"}),  # e6 — safe from promotion square
        (0, 7, {"type": "black_rook"}),  # h8
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White pawn a7→a8 (promotion) — turn doesn't increment, pawn exchange required
    game = select_and_move_white_piece(game, 1, 0, 0, 0)

    # Exchange: replace pawn with knight on a8 (knight won't check king at e6)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][0][0] = [{"type": "white_knight"}]
    game = api.update_game_state(
        game["id"], api.GameStateRequest(**game_on_next_turn), Response()
    )

    result = get_replay(game["id"])
    assert len(result) >= 2

    # Should show the promoted knight on a8 in a later state
    has_knight = any(
        s["board_state"][0][0] is not None
        and any(p["type"] == "white_knight" for p in s["board_state"][0][0])
        for s in result
    )
    assert has_knight


def test_bishop_3_stack_debuff_replay(game):
    """White bishop triggers 3rd debuff stack on black piece → capture/spare resolves.

    White moves first. Bishop moves to threaten a 2-debuff piece, triggering 3rd stack.
    Then black responds.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (5, 4, {"type": "white_bishop", "energize_stacks": 0}),  # e3
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (3, 6, {"type": "black_pawn", "pawn_buff": 0, "bishop_debuff": 2}),  # g5 with 2 stacks
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White bishop e3→g5 area — need to move to square that threatens g5=[3,6]
    # Bishop at e3=[5,4] can go to f4=[4,5], g5=[3,6] (that's the pawn square — capture)
    # Or f2=[6,5], d4=[4,3], etc.
    # To THREATEN (not capture) the pawn to add debuff, bishop needs to move to a square
    # where g5 is in its threat range. f4=[4,5] threatens g5=[3,6] diagonally. Yes!
    game = select_and_move_white_piece(game, 5, 4, 4, 5)  # Be3→f4 (threatens g5, triggers 3rd debuff)

    # After 3rd debuff, verify it triggered
    assert any(p.get("bishop_debuff") == 3 for p in (game["board_state"][3][6] or []))

    # Capture the debuffed pawn (same pattern as test_full_bishop_debuff_capture)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_pawn")
    game_on_next_turn["board_state"][3][6] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [3, 6],
        "type": "black_pawn"
    })
    game = api.update_game_state(
        game["id"], api.GameStateRequest(**game_on_next_turn), Response()
    )

    # Debuff capture now increments the turn (bug fix). Black responds.
    game = select_and_move_black_piece(game, 0, 0, 0, 1)  # Ra8→b8

    result = get_replay(game["id"])
    assert len(result) >= 3

    # Verify the debuff + capture sequence appears
    has_debuff = any(
        any(p.get("bishop_debuff") == 3
            for row in s["board_state"] for sq in row for p in (sq or []))
        for s in result
    )
    assert has_debuff
    has_capture = any("black_pawn" in s.get("captured_pieces", {}).get("white", []) for s in result)
    assert has_capture


# ---------------------------------------------------------------------------
# Shop/Purchase tests
# ---------------------------------------------------------------------------

def test_purchase_replay(game):
    """Player buys a piece → replay includes the purchase state."""
    game_setup = copy.deepcopy(game)
    game_setup["gold_count"]["white"] = 10
    game_setup["previous_state"] = copy.deepcopy(game_setup)
    game = api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**game_setup), Response()
    )

    game = select_and_move_white_piece(game, 6, 0, 5, 0)  # a2→a3
    game = select_and_move_black_piece(game, 1, 0, 2, 0)  # a7→a6

    # Purchase a pawn on an empty square
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][5][3] = [{"type": "white_pawn", "pawn_buff": 0}]
    game = api.update_game_state(
        game["id"], api.GameStateRequest(**game_on_next_turn), Response()
    )

    result = get_replay(game["id"])
    assert len(result) >= 2


# ---------------------------------------------------------------------------
# Neutral monster tests
# ---------------------------------------------------------------------------

def test_monster_spawn_replay(game):
    """White moves (turn 8→9), black moves (turn 9→10) → monsters spawn at turn 10."""
    game_setup = copy.deepcopy(game)
    game_setup["turn_count"] = 8  # white's turn
    game_setup["previous_state"] = copy.deepcopy(game_setup)
    game = api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**game_setup), Response()
    )

    # White moves at turn 8
    game = select_and_move_white_piece(game, 6, 0, 5, 0)  # a2→a3

    # Black moves at turn 9 → turn becomes 10 → monsters spawn
    game = select_and_move_black_piece(game, 1, 0, 2, 0)  # a7→a6

    result = get_replay(game["id"])
    assert len(result) >= 2

    # Last state should be turn 10 with monsters
    last = result[-1]
    assert last["turn_count"] == 10
    dragon_square = last["board_state"][4][7]
    assert dragon_square is not None
    assert any(p.get("type") == "neutral_dragon" for p in dragon_square)


def test_monster_damage_replay(game):
    """White knight moves adjacent to dragon → dragon takes damage."""
    game = setup_custom_board(game, [
        (7, 5, {"type": "white_king"}),  # f1 (off home square)
        (7, 6, {"type": "white_knight"}),  # g1
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (4, 7, {"type": "neutral_dragon", "health": 5, "turn_spawned": 0}),
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # Knight g1=[7,6] → h3=[5,7] (adjacent to dragon at [4,7])
    game = select_and_move_white_piece(game, 7, 6, 5, 7)

    result = get_replay(game["id"])
    assert len(result) >= 1
    assert get_snapshot_count(game["id"]) >= 2

    # Dragon should have taken damage
    last = result[-1]
    dragon_square = last["board_state"][4][7]
    assert dragon_square is not None
    dragon = next(p for p in dragon_square if p["type"] == "neutral_dragon")
    assert dragon["health"] < 5


def test_monster_kill_and_buff_replay(game):
    """White pawn kills 1-HP dragon → dragon buff granted to white."""
    game = setup_custom_board(game, [
        (7, 5, {"type": "white_king"}),  # f1
        (6, 7, {"type": "white_pawn", "pawn_buff": 0}),  # h2
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (4, 7, {"type": "neutral_dragon", "health": 1, "turn_spawned": 0}),
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # Pawn h2=[6,7] → h3=[5,7] (adjacent to dragon → kills it)
    game = select_and_move_white_piece(game, 6, 7, 5, 7)

    result = get_replay(game["id"])
    assert len(result) >= 1

    last = result[-1]
    dragon_stacks = last.get("neutral_buff_log", {}).get("white", {}).get("dragon", {}).get("stacks", 0)
    assert dragon_stacks >= 1


def test_monster_attack_on_piece_replay(game):
    """Dragon kills an adjacent black pawn via neutral_kill_mark → pawn enters graveyard.

    The monster attack mechanic works over 2 turns: first the piece is marked, then killed
    when turn_count reaches the mark value. This test sets up a pre-marked piece and
    triggers the kill by advancing the turn.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (6, 0, {"type": "white_pawn", "pawn_buff": 0}),  # a2
        (0, 4, {"type": "black_king"}),
        (0, 0, {"type": "black_rook"}),
        (4, 7, {"type": "neutral_dragon", "health": 5, "turn_spawned": 0}),
        # Black pawn adjacent to dragon, marked for kill on turn 2
        (3, 7, {"type": "black_pawn", "pawn_buff": 0, "neutral_kill_mark": 2}),
    ], turn_count=0, extra={
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White moves (turn 0→1)
    game = select_and_move_white_piece(game, 6, 0, 5, 0)  # a2→a3

    # Black moves (turn 1→2) — monster attack fires at turn 2, killing the pawn
    game = select_and_move_black_piece(game, 0, 0, 0, 1)  # Ra8→b8

    result = get_replay(game["id"])
    assert len(result) >= 2

    # The pawn should be in the graveyard in later states
    has_graveyard = any("black_pawn" in s.get("graveyard", []) for s in result)
    assert has_graveyard


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_pruning(game):
    """Play many turns → old snapshots are pruned beyond 10 turn_count window."""
    game_id = game["id"]

    # Fast-forward to turn 20
    game_setup = copy.deepcopy(game)
    game_setup["turn_count"] = 20
    game_setup["previous_state"] = copy.deepcopy(game_setup)
    game = api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**game_setup), Response()
    )

    game = select_and_move_white_piece(game, 6, 1, 5, 1)  # b2→b3

    old_snaps = mongo_client["game_db"]["game_state_history"].count_documents({
        "game_id": game_id,
        "turn_count": {"$lt": 11}
    })
    assert old_snaps == 0


def test_game_over_checkmate_replay(game):
    """White delivers checkmate → replay shows the final move and defeat flag.

    Back rank mate: white rook delivers checkmate on the 8th rank.
    King trapped by own pawns.
    """
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (2, 0, {"type": "white_rook"}),  # a6
        (0, 4, {"type": "black_king"}),  # e8
        (1, 3, {"type": "black_pawn", "pawn_buff": 0}),  # d7
        (1, 4, {"type": "black_pawn", "pawn_buff": 0}),  # e7
        (1, 5, {"type": "black_pawn", "pawn_buff": 0}),  # f7
    ], turn_count=20, extra={  # high turn for full rook range
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # White rook a6=[2,0] → a8=[0,0] — back rank mate
    game = select_and_move_white_piece(game, 2, 0, 0, 0)

    result = get_replay(game["id"])
    assert len(result) >= 1

    last = result[-1]
    assert last["black_defeat"] == True


def test_stun_skip_replay(game):
    """Realistic stun skip: black queen moves to stun white pieces → white can't move → skip.

    Turn 1: Black queen starts away from white pieces, moves adjacent to stun them.
    Turn 2: White is boxed in + all stunned → auto-skip.
    The replay shows the queen's stun move and the resulting skip.
    """
    # White king at e1 boxed by own pawns. d1 and f1 are already stunned from earlier.
    # Black queen at a3 will move to e3 (adjacent to d2, e2, f2) to stun the remaining
    # 3 pawns. After that, ALL 5 pawns are stunned and king can't move → skip.
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),  # e1
        (6, 3, {"type": "white_pawn", "pawn_buff": 0}),  # d2 — will get stunned by queen
        (6, 4, {"type": "white_pawn", "pawn_buff": 0}),  # e2 — will get stunned by queen
        (6, 5, {"type": "white_pawn", "pawn_buff": 0}),  # f2 — will get stunned by queen
        (7, 3, {"type": "white_pawn", "pawn_buff": 0, "is_stunned": True, "turn_stunned_for": 20}),  # d1 — already stunned
        (7, 5, {"type": "white_pawn", "pawn_buff": 0, "is_stunned": True, "turn_stunned_for": 20}),  # f1 — already stunned
        (5, 0, {"type": "black_queen"}),  # a3 — starts away, will move to e3
        (0, 4, {"type": "black_king"}),
    ], turn_count=7, extra={  # odd turn = black's turn
        "castle_log": {
            "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
            "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True}
        }
    })

    # Black queen a3=[5,0] → e3=[5,4] — moves adjacent to white pawns WITHOUT capturing → stuns them
    game = select_and_move_black_piece(game, 5, 0, 5, 4)  # Qa3→e3

    # After stun: turn increments to 8 (white's turn). King boxed in + all pieces stunned → skip
    result = get_replay(game["id"])
    assert len(result) >= 1

    # Turn should have jumped past 8 (white's stun skip)
    last = result[-1]
    assert last["turn_count"] >= 9
