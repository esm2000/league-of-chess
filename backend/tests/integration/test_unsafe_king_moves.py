"""Integration tests for unsafe_king_moves — squares the king can reach but can't move to."""

import copy

from fastapi import Response

import src.api as api
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_white_piece,
    select_and_move_white_piece,
    select_and_move_black_piece,
)


def setup_custom_board(game, pieces, turn_count=0, extra=None):
    game = clear_game(game)
    g = copy.deepcopy(game)
    for row, col, piece in pieces:
        g["board_state"][row][col] = [piece] if isinstance(piece, dict) else piece
    g["turn_count"] = turn_count
    if extra:
        for k, v in extra.items():
            g[k] = v
    g["previous_state"] = copy.deepcopy(g)
    return api.update_game_state_no_restrictions(
        game["id"], api.GameStateRequest(**g), Response()
    )


CL = {
    "castle_log": {
        "white": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
        "black": {"has_king_moved": True, "has_left_rook_moved": True, "has_right_rook_moved": True},
    }
}


def test_king_selected_with_adjacent_enemy_rook(game):
    """Enemy rook on same file → some king moves are unsafe."""
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),       # e1
        (0, 4, {"type": "black_king"}),
        (3, 4, {"type": "black_rook"}),        # e5 — attacks e-file
    ], extra=CL)

    game = select_white_piece(game, 7, 4)

    # King at e1=[7,4] can reach d1,f1,d2,e2,f2. Rook on e5 attacks e-file.
    # Squares on e-file (e2=[6,4]) should be unsafe.
    unsafe = [tuple(m) for m in game["unsafe_king_moves"]]
    assert (6, 4) in unsafe  # e2 is attacked by rook on e-file
    assert len(game["possible_moves"]) > 0  # king still has safe moves


def test_king_selected_with_no_threats(game):
    """King in open area with no nearby enemies → no unsafe moves."""
    game = setup_custom_board(game, [
        (4, 4, {"type": "white_king"}),        # e4 — center, open
        (0, 0, {"type": "black_king"}),        # far away corner
    ], extra=CL)

    game = select_white_piece(game, 4, 4)

    assert game["unsafe_king_moves"] == []
    assert len(game["possible_moves"]) > 0


def test_non_king_piece_selected(game):
    """Selecting a non-king piece → unsafe_king_moves should be empty."""
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (6, 0, {"type": "white_pawn", "pawn_buff": 0}),
        (0, 4, {"type": "black_king"}),
    ], extra=CL)

    game = select_white_piece(game, 6, 0)  # select the pawn

    assert game["unsafe_king_moves"] == []


def test_unsafe_cleared_after_move(game):
    """After king moves, unsafe_king_moves should be cleared."""
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),
        (0, 4, {"type": "black_king"}),
        (3, 4, {"type": "black_rook"}),
    ], extra=CL)

    game = select_white_piece(game, 7, 4)
    assert len(game["unsafe_king_moves"]) > 0  # has unsafe moves

    # Move king to a safe square
    safe_moves = game["possible_moves"]
    assert len(safe_moves) > 0
    target = safe_moves[0]

    game = select_and_move_white_piece(game, 7, 4, target[0], target[1])
    assert game["unsafe_king_moves"] == []  # cleared after move


def test_king_in_check_shows_unsafe(game):
    """King in check → unsafe_king_moves shows attacked escape squares."""
    game = setup_custom_board(game, [
        (7, 4, {"type": "white_king"}),         # e1
        (0, 4, {"type": "black_king"}),
        (7, 0, {"type": "black_rook"}),          # a1 — checks king along rank 1
    ], extra=CL)

    # King is in check from rook on a1 (same rank)
    game = select_white_piece(game, 7, 4)

    # Squares on rank 1 (row 7) that the rook attacks should be unsafe
    unsafe = [tuple(m) for m in game["unsafe_king_moves"]]
    # d1=[7,3] and f1=[7,5] are on the same rank as the rook — should be unsafe
    # (rook at a1 attacks the entire 1st rank)
    assert any(m[0] == 7 for m in unsafe)  # at least some rank-1 squares are unsafe


def test_multiple_threats(game):
    """King threatened by pieces on different lines → multiple unsafe squares."""
    game = setup_custom_board(game, [
        (4, 4, {"type": "white_king"}),         # e4
        (0, 4, {"type": "black_king"}),
        (2, 4, {"type": "black_rook"}),          # e6 — attacks e-file
        (2, 2, {"type": "black_bishop", "energize_stacks": 0}),  # c6 — attacks diagonal
    ], extra=CL)

    game = select_white_piece(game, 4, 4)

    unsafe = [tuple(m) for m in game["unsafe_king_moves"]]
    # Should have multiple unsafe squares from both the rook (e-file) and bishop (diagonal)
    assert len(unsafe) >= 2
