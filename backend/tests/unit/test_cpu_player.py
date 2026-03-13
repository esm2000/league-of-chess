"""Unit tests for CPU player move generation."""

import copy

from mocks.empty_game import empty_game
from src.cpu_player import (
    get_all_valid_moves,
    get_marked_for_death_moves,
    _get_raw_moves,
    _move_leaves_king_safe,
)


def _make_game(**overrides):
    """Create a game state from empty_game with optional overrides."""
    game = copy.deepcopy(empty_game)
    game["previous_state"] = copy.deepcopy(empty_game)
    for key, value in overrides.items():
        game[key] = value
    return game


def test_get_all_valid_moves_single_pawn():
    """A lone black pawn on row 3 should be able to move forward (to row 4)."""
    game = _make_game(turn_count=1)
    game["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    move_destinations = [m["to_pos"] for m in valid_moves if m["from_pos"] == [3, 3]]
    assert [4, 3] in move_destinations
    assert all(m["type"] == "move" for m in valid_moves if m["from_pos"] == [3, 3])


def test_get_all_valid_moves_pawn_capture():
    """A black pawn should be able to capture a diagonally adjacent white piece."""
    game = _make_game(turn_count=1)
    game["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][4][2] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    capture_moves = [m for m in valid_moves if m["type"] == "capture" and m["from_pos"] == [3, 3]]
    capture_destinations = [m["to_pos"] for m in capture_moves]
    assert [4, 2] in capture_destinations


def test_get_all_valid_moves_knight():
    """A black knight should have L-shaped moves."""
    game = _make_game(turn_count=1)
    game["board_state"][4][4] = [{"type": "black_knight"}]
    game["board_state"][0][0] = [{"type": "black_king"}]
    game["board_state"][7][7] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    knight_moves = [m for m in valid_moves if m["from_pos"] == [4, 4]]
    assert len(knight_moves) > 0


def test_get_all_valid_moves_excludes_stunned_pieces():
    """Stunned pieces should not generate any moves."""
    game = _make_game(turn_count=1)
    game["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0, "is_stunned": True, "turn_stunned_for": 1}]
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    pawn_moves = [m for m in valid_moves if m["from_pos"] == [3, 3]]
    assert len(pawn_moves) == 0


def test_get_all_valid_moves_filters_moves_leaving_king_in_check():
    """A pinned piece should not be able to move if it exposes the king to check."""
    # Black king at [0, 0], black pawn at [1, 1], white bishop at [2, 2]
    # The pawn is pinned — moving it exposes the king to the bishop
    game = _make_game(turn_count=1)
    game["board_state"][0][0] = [{"type": "black_king"}]
    game["board_state"][1][1] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][2][2] = [{"type": "white_bishop", "energize_stacks": 0}]
    game["board_state"][7][7] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    # The pawn at [1,1] should have no valid moves because it's pinned
    pawn_moves = [m for m in valid_moves if m["from_pos"] == [1, 1]]
    assert len(pawn_moves) == 0


def test_get_all_valid_moves_king_avoids_unsafe_squares():
    """King should not be able to move into check."""
    game = _make_game(turn_count=1)
    game["board_state"][0][0] = [{"type": "black_king"}]
    game["board_state"][7][7] = [{"type": "white_king"}]
    # White rook on row 1 — controls the entire row
    game["board_state"][1][7] = [{"type": "white_rook"}]

    valid_moves = get_all_valid_moves(game)

    king_moves = [m for m in valid_moves if m["from_pos"] == [0, 0]]
    king_destinations = [m["to_pos"] for m in king_moves]
    # King should NOT move to row 1 (controlled by rook)
    assert [1, 0] not in king_destinations
    assert [1, 1] not in king_destinations
    # King should be able to move to [0, 1] (same row, safe)
    assert [0, 1] in king_destinations


def test_get_all_valid_moves_in_check_must_escape():
    """When in check, only moves that escape check should be valid."""
    game = _make_game(turn_count=1)
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]
    # White rook gives check from [0, 7]
    game["board_state"][0][7] = [{"type": "white_rook"}]
    game["check"] = {"white": False, "black": True}
    # Black pawn can't help
    game["board_state"][5][0] = [{"type": "black_pawn", "pawn_buff": 0}]

    valid_moves = get_all_valid_moves(game)

    # The pawn at [5,0] can't resolve the check — only king moves should be valid
    pawn_moves = [m for m in valid_moves if m["from_pos"] == [5, 0]]
    assert len(pawn_moves) == 0

    # King should have escape moves (moving off the first rank)
    king_moves = [m for m in valid_moves if m["from_pos"] == [0, 4]]
    assert len(king_moves) > 0


def test_get_marked_for_death_moves():
    """Should find all black pieces marked for death."""
    game = _make_game(turn_count=1)
    game["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0, "marked_for_death": True}]
    game["board_state"][4][4] = [{"type": "black_knight", "marked_for_death": True}]
    game["board_state"][0][4] = [{"type": "black_king"}]

    sacrifice_moves = get_marked_for_death_moves(game)

    assert len(sacrifice_moves) == 2
    positions = [m["from_pos"] for m in sacrifice_moves]
    assert [3, 3] in positions
    assert [4, 4] in positions
    assert all(m["type"] == "sacrifice" for m in sacrifice_moves)


def test_get_all_valid_moves_castle():
    """King should be able to castle when conditions are met."""
    game = _make_game(turn_count=1)
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][0][7] = [{"type": "black_rook"}]
    game["board_state"][0][0] = [{"type": "black_rook"}]
    game["board_state"][7][4] = [{"type": "white_king"}]
    game["castle_log"] = {
        "white": {"has_king_moved": False, "has_left_rook_moved": False, "has_right_rook_moved": False},
        "black": {"has_king_moved": False, "has_left_rook_moved": False, "has_right_rook_moved": False},
    }

    valid_moves = get_all_valid_moves(game)

    castle_moves = [m for m in valid_moves if m["type"] == "castle"]
    castle_destinations = [m["to_pos"] for m in castle_moves]
    assert [0, 2] in castle_destinations  # queenside
    assert [0, 6] in castle_destinations  # kingside


def test_no_moves_for_white_pieces():
    """CPU should only generate moves for black pieces, not white."""
    game = _make_game(turn_count=1)
    game["board_state"][6][3] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]

    valid_moves = get_all_valid_moves(game)

    white_moves = [m for m in valid_moves if m["from_pos"] == [6, 3]]
    assert len(white_moves) == 0
