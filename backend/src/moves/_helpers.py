"""Shared move generation helpers — file control, dragon buff collision, baron immunity."""

from __future__ import annotations

import copy

from src.types import BoardState, GameState, MoveResult, Piece, Position
from src.utils.piece_mechanics import enable_adjacent_bishop_captures

# moves list is either list of possible moves or list of possible captures
def filter_moves_for_file_control(moves_list: list, curr_position: Position, is_capture: bool = False) -> None:
    """Remove vertical moves that cross the center file boundary."""
    center_squares = [
        [2, 2], [2, 3], [2, 4], [2, 5],
        [3, 2], [3, 3], [3, 4], [3, 5],
        [4, 2], [4, 3], [4, 4], [4, 5],
        [5, 2], [5, 3], [5, 4], [5, 5]
    ]
    index = 0
    while index < len(moves_list):
        move = moves_list[index] if not is_capture else moves_list[index][0]

        # determine if it's a vertical move
        if curr_position[1] == move[1]:
            # eliminate move if row 3 or 4 is passed and curr_position is not a center square
            if (
                (curr_position[0] < 2 and move[0] > 5) or
                (curr_position[0] > 5 and move[0] < 2)
            ) and (curr_position not in center_squares):
                moves_list.pop(index)
                continue
        index += 1


def process_possible_moves_dict(curr_game_state: GameState, curr_position: Position, side: str, possible_moves_dict: MoveResult, is_king: bool = False) -> MoveResult:
    """Post-process moves: apply bishop captures, file control, sword filtering, dedup."""
    possible_moves_dict = enable_adjacent_bishop_captures(curr_game_state, side, possible_moves_dict)

    # remove moves and captures that involve moving to a sword in stone buff unless we're dealing with a king
    if not is_king and curr_game_state["sword_in_the_stone_position"]:
        possible_moves_dict["possible_moves"] = [move for move in possible_moves_dict["possible_moves"] if move != curr_game_state["sword_in_the_stone_position"]]
        possible_moves_dict["possible_captures"] = [capture for capture in possible_moves_dict["possible_captures"] if capture[0] != curr_game_state["sword_in_the_stone_position"]]

    # remove duplicates
    possible_moves_with_no_duplicates = []
    for entry in possible_moves_dict["possible_moves"]:
        if entry not in possible_moves_with_no_duplicates:
            possible_moves_with_no_duplicates.append(entry)
    possible_moves_dict["possible_moves"] = possible_moves_with_no_duplicates

    possible_captures_with_no_duplicates = []
    for entry in possible_moves_dict["possible_captures"]:
        if entry not in possible_captures_with_no_duplicates:
            possible_captures_with_no_duplicates.append(copy.deepcopy(entry))
    possible_moves_dict["possible_captures"] = possible_captures_with_no_duplicates

    # enforce file control - no vertical moves past the center of the board unless piece originates in center
    # apply filtering to both possible_moves and possible_captures
    filter_moves_for_file_control(possible_moves_dict["possible_moves"], curr_position)
    filter_moves_for_file_control(possible_moves_dict["possible_captures"], curr_position, is_capture=True)

    if "castle_moves" not in possible_moves_dict:
        possible_moves_dict["castle_moves"] = []
    return possible_moves_dict


def _add_marked_for_death_threats(possible_moves: list[Position], threatening_move: list[Position], opposing_side: str, board_state: BoardState) -> None:
    """5-dragon-stack marked-for-death: add king threats for squares adjacent to landing squares.
    Only kings are added to threatening_move (for check detection). Non-king pieces are
    intentionally omitted from possible_captures because the opponent chooses which
    marked-for-death piece dies. That resolution happens in the game update pipeline."""
    adjacent_deltas = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]
    for possible_move in possible_moves:
        for delta in adjacent_deltas:
            adj = [possible_move[0] + delta[0], possible_move[1] + delta[1]]
            if adj[0] < 0 or adj[0] > 7 or adj[1] < 0 or adj[1] > 7:
                continue
            square = board_state[adj[0]][adj[1]]
            if square and any(opposing_side in piece.get("type", "") for piece in square):
                if any("king" in piece.get("type", "") for piece in square):
                    threatening_move.append(possible_move)


def _can_ignore_ally_collision(square: list[Piece] | None, side: str, dragon_buff: int) -> bool:
    """Check if dragon buff allows passing through allies on this square."""
    if dragon_buff == 3:
        return any(piece.get("type") == f"{side}_pawn" for piece in square or [])
    if dragon_buff >= 4:
        return any(side in piece.get("type") for piece in square or [])
    return False


def _is_path_clear(squares: list[list[Piece] | None], side: str, opposing_side: str, dragon_buff: int) -> bool:
    """Check if all squares in a path are passable given dragon buff tier."""
    def is_square_passable(square):
        if not square:
            return True
        has_neutral = any("neutral" in piece.get("type", "") for piece in square)
        if dragon_buff >= 4:
            return (has_neutral and all(opposing_side not in piece.get("type", "") for piece in square)) or \
                   any(side in piece.get("type", "") for piece in square)
        elif dragon_buff == 3:
            return (has_neutral and all(opposing_side not in piece.get("type", "") for piece in square)) or \
                   any(f"{side}_pawn" == piece.get("type", "") for piece in square)
        else:
            return has_neutral and all(side not in piece.get("type", "") and opposing_side not in piece.get("type", "") for piece in square)
    return all(is_square_passable(square) for square in squares)


def _is_diagonal_path_blocked(squares: list[list[Piece] | None], side: str, dragon_buff: int) -> bool:
    """Check if any intermediate square blocks a diagonal capture path."""
    for s in squares:
        if not s:
            continue
        if dragon_buff >= 4:
            if not all(side in p.get("type", "") for p in s):
                return True
        elif dragon_buff == 3:
            if not all(f"{side}_pawn" == p.get("type", "") for p in s):
                return True
        else:
            return True
    return False


def _is_baron_immune(square: list[Piece], opposing_side: str, baron_buff_active: bool) -> bool:
    """Check if an opposing pawn on this square is immune due to baron buff."""
    return not baron_buff_active and \
           any(piece.get("baron_nashor_buff") and f"{opposing_side}_pawn" == piece.get("type") for piece in square)


def _add_forward_capture(possible_moves: list[Position], possible_captures: list[list[Position]], threatening_move: list[Position], target_square: list[Piece], move_position: Position, opposing_side: str) -> None:
    """Add a forward capture or king threat based on what's on the target square."""
    if any(f"{opposing_side}_king" == piece.get("type", "") for piece in target_square) and not threatening_move:
        threatening_move.append(move_position)
    elif any(opposing_side in piece.get("type", "") for piece in target_square):
        possible_moves.append(move_position)
        possible_captures.append([move_position, move_position])
