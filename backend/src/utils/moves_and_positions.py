"""Position-in-play selection, move determination, and turn-side validation."""

import traceback

from fastapi import HTTPException

from src.log import logger
from src.types import GameState, MovedPiece
import src.moves as moves
from .check_checkmate import trim_king_moves


def determine_possible_moves(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], player: bool, reset_position_in_play: bool, is_pawn_exchange_required_this_turn: bool) -> None:
    """Compute and store legal moves for the selected position_in_play."""
    has_non_neutral_piece_moved = False
    for moved_piece in moved_pieces:
        if moved_piece["side"] == "neutral":
            continue
        has_non_neutral_piece_moved = True
    if has_non_neutral_piece_moved and reset_position_in_play:
        new_game_state["position_in_play"] = [None, None]
    if new_game_state["position_in_play"][0] is not None:
        square = new_game_state["board_state"][new_game_state["position_in_play"][0]][new_game_state["position_in_play"][1]]
        piece_in_play = None
        for piece in square:
            if (player and "white" in piece.get('type')) \
                or (not player and "black" in piece.get('type')) \
                or ("king" in piece.get('type')):
                piece_in_play = piece

        if not piece_in_play:
            error_msg = f"Invalid position_in_play in potential new game state, no piece present ({new_game_state['position_in_play']})"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        try:
            moves_info = moves.get_moves(old_game_state, new_game_state, new_game_state["position_in_play"], piece)
            if "king" in piece.get("type", ""):
                side = piece["type"].split("_")[0]
                pre_trim = set(tuple(m) for m in moves_info["possible_moves"])
                moves_info = trim_king_moves(moves_info, old_game_state, new_game_state, side)
                post_trim = set(tuple(m) for m in moves_info["possible_moves"])
                new_game_state["unsafe_king_moves"] = [list(m) for m in pre_trim - post_trim]
            else:
                new_game_state["unsafe_king_moves"] = []
        except Exception as e:
            logger.error(f"Unable to determine move for {piece} due to: {traceback.format_exc()}")

        new_game_state["possible_moves"] = moves_info["possible_moves"]
        new_game_state["possible_captures"] = moves_info["possible_captures"]

    # Compute castle_moves for the side about to move, independent of position_in_play
    side_to_move = "white" if not new_game_state["turn_count"] % 2 else "black"
    start_row = 7 if side_to_move == "white" else 0
    king_square = new_game_state["board_state"][start_row][4] or []
    king_piece = next((p for p in king_square if p.get("type") == f"{side_to_move}_king"), None)

    castle_moves = []
    if king_piece and not new_game_state["castle_log"][side_to_move]["has_king_moved"] \
            and not new_game_state["check"][side_to_move]:
        try:
            king_moves = moves.get_moves(old_game_state, new_game_state, [start_row, 4], king_piece)
            king_moves = trim_king_moves(king_moves, old_game_state, new_game_state, side_to_move)
            castle_moves = king_moves.get("castle_moves", [])
        except Exception:
            logger.error(f"Unable to compute castle_moves for {side_to_move} king: {traceback.format_exc()}")
    new_game_state["castle_moves"] = castle_moves

    if is_pawn_exchange_required_this_turn:
        new_game_state["possible_moves"] = []
        new_game_state["possible_captures"] = []
        new_game_state["castle_moves"] = []


def was_a_new_position_in_play_selected(moved_pieces: list[MovedPiece], old_game_state: GameState, new_game_state: GameState) -> bool:
    """Return True if the client selected a new piece without moving any piece."""
    return not len([mp for mp in moved_pieces if mp["previous_position"][0] is not None and mp["current_position"][0] is not None]) and \
    old_game_state["position_in_play"] != new_game_state["position_in_play"]


def does_position_in_play_match_turn(old_game_state: GameState, new_game_state: GameState) -> bool:
    """Return True if the position_in_play contains a piece matching the side to move."""
    side_that_should_be_moving = "white" if not old_game_state["turn_count"] % 2 else "black"
    position = new_game_state["position_in_play"]
    square = old_game_state["board_state"][position[0]][position[1]] or []

    if not square:
        logger.error(f"Position in play validation failed: No piece at position {position}")
        return False

    for piece in square:
        if side_that_should_be_moving in piece.get("type", ""):
            return True

    piece_types = [piece.get("type", "unknown") for piece in square]
    logger.error(f"Position in play validation failed: {side_that_should_be_moving} cannot move pieces at {position}. Found pieces: {piece_types}")
    return False
