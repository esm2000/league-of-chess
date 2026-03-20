"""Check, checkmate, and stalemate detection with king safety analysis."""

import copy

from src.log import logger
from src.types import GameState, MoveResult, MovedPiece, Position, UnsafePositions
import src.moves as moves
from .monsters import MONSTER_INFO


def get_unsafe_positions_for_kings(old_game_state: GameState, new_game_state: GameState) -> UnsafePositions:
    """Compute all squares attacked by each side's pieces plus neutral monster zones."""
    output = {
        "white": set(),
        "black": set()
    }

    # find king positions
    king_positions = {}
    for row in range(len(new_game_state["board_state"])):
        for col in range(len(new_game_state["board_state"][0])):
            square = new_game_state["board_state"][row][col] or []
            for piece in square:
                if "king" in piece.get("type"):
                    side = piece["type"].split("_")[0]
                    king_positions[side] = [row, col]

    possible_king_locations = {"white": [], "black": []}
    for side in king_positions:
        row, col = king_positions[side]

        piece = None
        for p in (new_game_state["board_state"][row][col] or []):
            if "king" in p.get("type"):
                piece = p

        if piece is None:
            logger.error(f"Unable to find location of {side} king when calculating unsafe positions")
            continue

        moves_info = moves.get_moves(old_game_state, new_game_state, [row, col], piece)

        positions = [tuple(possible_move) for possible_move in moves_info["possible_moves"]]
        positions += [tuple(possible_capture[0]) for possible_capture in moves_info["possible_captures"]]
        positions += [tuple(move) for move in moves_info["threatening_move"]]

        possible_king_locations[side] = list(set(positions + possible_king_locations[side]))


    old_game_states = [old_game_state]
    new_game_states = [new_game_state]

    for side in possible_king_locations:
        for possible_king_location in possible_king_locations[side]:
            if side not in king_positions:
                continue
            current_king_location = king_positions[side]

            new_game_state_copy = copy.deepcopy(new_game_state)
            simulated_game_state = copy.deepcopy(new_game_state)

            simulated_game_state["board_state"][possible_king_location[0]][possible_king_location[1]] = simulated_game_state["board_state"][current_king_location[0]][current_king_location[1]]
            simulated_game_state["board_state"][current_king_location[0]][current_king_location[1]] = None

            simulated_game_state["turn_count"] += 1
            old_game_states.append(new_game_state_copy)
            new_game_states.append(simulated_game_state)

    adjacent_deltas = [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, -1], [1, -1], [-1, 1]]
    for i in range(len(old_game_states)):
        ogs = old_game_states[i]
        ngs = new_game_states[i]
        for row in range(len(ngs["board_state"])):
            for col in range(len(ngs["board_state"][0])):
                square = ngs["board_state"][row][col] or []
                for piece in square:
                    if "king" not in piece.get("type", "") and ("white" in piece.get("type", "") or "black" in piece.get("type", "")):
                        side = piece["type"].split("_")[0]
                        opposite_side = "white" if side == "black" else "black"
                        moves_info = moves.get_moves(ogs, ngs, [row, col], piece)
                        output[opposite_side] = output[opposite_side].union({tuple(threatening_move) for threatening_move in moves_info["threatening_move"]})
                    elif "king" in piece.get("type", ""):
                        side = piece["type"].split("_")[0]
                        opposite_side = "white" if side == "black" else "black"
                        for delta in adjacent_deltas:
                            if delta == [0, 0]:
                                continue
                            position = (row+delta[0], col+delta[1])
                            if position[0] < 0 or position[0] >= 8 or position[1] < 0 or position[1] >= 8:
                                continue
                            adjacent_square = ngs["board_state"][position[0]][position[1]] or []
                            if any("king" in p.get("type") for p in adjacent_square):
                                output[side] = output[side].union({position})
                    elif "neutral" in piece.get("type", ""):
                        for delta in adjacent_deltas:
                            position = (row+delta[0], col+delta[1])
                            if position[0] < 0 or position[0] >= 8 or position[1] < 0 or position[1] >= 8:
                                continue
                            output["white"] = output["white"].union({position})
                            output["black"] = output["black"].union({position})

    output = {side: [list(position_tuple) for position_tuple in output[side]] for side in output}
    return output


def manage_check_status(old_game_state: GameState, new_game_state: GameState) -> None:
    """Update check flags based on king positions vs unsafe squares. Consumes Divine Right if applicable."""
    unsafe_positions = get_unsafe_positions_for_kings(old_game_state, new_game_state)
    not_in_check = {"white": True, "black": True}
    for side in unsafe_positions:
        for unsafe_position in unsafe_positions[side]:
            square = new_game_state["board_state"][unsafe_position[0]][unsafe_position[1]] or []

            for piece in square:
                if piece.get("type", "") == f"{side}_king":
                    if not piece.get("check_protection", 0):
                        new_game_state["check"][side] = True
                        not_in_check[side] = False
                    else:
                        piece["check_protection"] -= 1

    for side in not_in_check:
        if not_in_check[side]:
            new_game_state["check"][side] = False


def _has_marked_for_death_pieces(game_state: GameState, side: str) -> bool:
    """Check if the given side has any pieces marked for death on the board."""
    for row in game_state["board_state"]:
        for square in row:
            for piece in square or []:
                if side in piece.get("type", "") and piece.get("marked_for_death", False):
                    return True
    return False


def end_game_on_checkmate(old_game_state: GameState, new_game_state: GameState) -> None:
    """Set defeat flag if the side to move is in checkmate."""
    side_that_should_be_moving_next_turn = "white" if old_game_state["turn_count"] % 2 else "black"

    if _has_marked_for_death_pieces(new_game_state, side_that_should_be_moving_next_turn):
        return

    if new_game_state["check"][side_that_should_be_moving_next_turn] and \
    not can_king_move(old_game_state, new_game_state) and \
    not can_other_pieces_prevent_check(side_that_should_be_moving_next_turn, old_game_state, new_game_state):
        logger.info(f"{side_that_should_be_moving_next_turn.upper()} DEFEAT set to True: Checkmate - King in check with no escape moves and no pieces can prevent check")
        new_game_state[f"{side_that_should_be_moving_next_turn}_defeat"] = True


def can_king_move(old_game_state: GameState, new_game_state: GameState, turn_incremented: bool = False) -> bool:
    """Return True if the king for the side to move has any legal moves."""
    new_game_turn_count = new_game_state["turn_count"]
    if not turn_incremented:
        side_that_should_be_moving_next_turn = "white" if not new_game_turn_count % 2 else "black"
    else:
        side_that_should_be_moving_next_turn = "white" if new_game_turn_count % 2 else "black"

    output = False
    for i in range(len(new_game_state["board_state"])):
        for j in range(len(new_game_state["board_state"][0])):
            square = new_game_state["board_state"][i][j]

            if square:
                for piece in square:
                    if piece.get("type", "") == f"{side_that_should_be_moving_next_turn}_king":
                        moves_info = moves.get_moves_for_king(
                            new_game_state,
                            old_game_state,
                            [i, j]
                        )
                        moves_info = trim_king_moves(moves_info, old_game_state, new_game_state, side_that_should_be_moving_next_turn)
                        output = len(moves_info["possible_moves"]) > 0
    return output


def can_other_pieces_prevent_check(side: str, old_game_state: GameState, new_game_state: GameState) -> bool:
    """Return True if any non-king piece can block or capture to escape check."""
    for row in range(len(new_game_state["board_state"])):
        for col in range(len(new_game_state["board_state"][0])):
            square = new_game_state["board_state"][row][col] or []
            for piece in square:
                if "king" not in piece.get("type") and side in piece.get("type"):
                    moves_info = moves.get_moves(old_game_state, new_game_state, [row, col], piece)

                    for possible_move in moves_info["possible_moves"]:
                        new_game_state_copy = copy.deepcopy(new_game_state)
                        simulated_game_state = copy.deepcopy(new_game_state)

                        simulated_game_state["board_state"][possible_move[0]][possible_move[1]] = simulated_game_state["board_state"][row][col]
                        simulated_game_state["board_state"][row][col] = None
                        manage_check_status(new_game_state_copy, simulated_game_state)
                        if not simulated_game_state["check"][side]:
                            return True

                    for possible_capture in moves_info["possible_captures"]:
                        new_game_state_copy = copy.deepcopy(new_game_state)
                        simulated_game_state = copy.deepcopy(new_game_state)

                        simulated_game_state["board_state"][possible_capture[0][0]][possible_capture[0][1]] = simulated_game_state["board_state"][row][col]
                        simulated_game_state["board_state"][possible_capture[1][0]][possible_capture[1][1]] = None
                        manage_check_status(new_game_state_copy, simulated_game_state)
                        if not simulated_game_state["check"][side]:
                            return True
    return False


def trim_king_moves(moves_info: MoveResult, old_game_state: GameState, new_game_state: GameState, side: str) -> MoveResult:
    """Remove king moves that land on unsafe squares, including castle moves through attacked squares."""
    unsafe_positions = get_unsafe_positions_for_kings(old_game_state, new_game_state)
    trimmed_moves_info = trim_moves(moves_info, unsafe_positions[side])

    # Filter castle moves where king passes through or lands on an attacked square
    unsafe_set = set(tuple(p) for p in unsafe_positions[side])
    start_row = 7 if side == "white" else 0
    i = 0
    while i < len(trimmed_moves_info.get("castle_moves", [])):
        target_col = trimmed_moves_info["castle_moves"][i][1]
        is_queenside = target_col == 2
        transit_cols = [3, 2] if is_queenside else [5, 6]
        if any((start_row, col) in unsafe_set for col in transit_cols):
            trimmed_moves_info["castle_moves"].pop(i)
        else:
            i += 1

    return trimmed_moves_info


def trim_moves(moves_info: MoveResult, unsafe_position_for_one_side: list[Position]) -> MoveResult:
    """Remove moves and captures whose destinations are in the unsafe positions list."""
    moves_info_copy = copy.deepcopy(moves_info)
    unsafe_positions_set = set([tuple(position) for position in unsafe_position_for_one_side])

    i = 0
    while i < len(moves_info_copy["possible_moves"]):
        if tuple(moves_info_copy["possible_moves"][i]) in unsafe_positions_set:
            moves_info_copy["possible_moves"].pop(i)
        else:
            i += 1

    i = 0
    while i < len(moves_info_copy["possible_captures"]):
        if tuple(moves_info_copy["possible_captures"][i][0]) in unsafe_positions_set:
            moves_info_copy["possible_captures"].pop(i)
        else:
            i += 1

    return moves_info_copy


def invalidate_game_if_player_moves_and_is_in_check(is_valid_game_state: bool, old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece]) -> bool:
    """Invalidate if a side moved while still in check (unless resolving marked-for-death)."""
    are_pieces_marked_for_death_in_old_game = False
    are_pieces_marked_for_death_in_new_game = False

    for row in range(len(old_game_state["board_state"])):
        for col in range(len(old_game_state["board_state"][row])):
            old_square = old_game_state["board_state"][row][col] or []
            new_square = new_game_state["board_state"][row][col] or []

            for piece in old_square:
                if piece.get("marked_for_death", False):
                    are_pieces_marked_for_death_in_old_game = True

            for piece in new_square:
                if piece.get("marked_for_death", False):
                    are_pieces_marked_for_death_in_new_game = True

    for moved_piece in moved_pieces:
        if moved_piece["previous_position"][0] is not None and moved_piece["previous_position"][1] is not None:
            side = moved_piece["side"]
            if side == "neutral":
                continue
            if new_game_state["check"][side] \
                and not is_check_due_to_neutral_monster_spawn_this_turn(old_game_state, new_game_state, side) \
                and not (are_pieces_marked_for_death_in_old_game and not are_pieces_marked_for_death_in_new_game):
                logger.error(f"{side} moved but is in check")
                is_valid_game_state = False
    return is_valid_game_state


def is_check_due_to_neutral_monster_spawn_this_turn(old_game_state: GameState, new_game_state: GameState, side: str) -> bool:
    """Return True if the check was caused by a neutral monster spawning this turn."""
    if old_game_state["check"][side]:
        return False

    simulated_game_state = copy.deepcopy(new_game_state)

    for monster in MONSTER_INFO:
        position = MONSTER_INFO[monster]["position"]
        square = simulated_game_state["board_state"][position[0]][position[1]] or []
        filtered_square = [piece for piece in square if "neutral" in piece.get("type")]
        simulated_game_state["board_state"][position[0]][position[1]] = filtered_square

    manage_check_status(new_game_state, simulated_game_state)
    return simulated_game_state["check"][side]


def set_next_king_as_position_in_play_if_in_check(old_game_state: GameState, new_game_state: GameState) -> bool:
    """Force position_in_play to the checked king. Returns False if king was set, True otherwise."""
    side_moving_next_turn = "white" if not bool(new_game_state["turn_count"] % 2) else "black"

    if new_game_state["check"][side_moving_next_turn] and \
    (not old_game_state["check"][side_moving_next_turn] or not is_position_in_play_valid_to_save_king(old_game_state, new_game_state)):
        for i in range(len(new_game_state["board_state"])):
            row = new_game_state["board_state"][i]
            for j in range(len(row)):
                square = row[j] or []
                for piece in square:
                    if piece["type"] == f"{side_moving_next_turn}_king":
                        new_game_state["position_in_play"] = [i, j]
                        return False
    return True


def is_position_in_play_valid_to_save_king(old_game_state: GameState, new_game_state: GameState) -> bool:
    """Return True if the piece at position_in_play can resolve check (capture or block)."""
    position_in_play = new_game_state["position_in_play"]
    if position_in_play == [None, None]:
        return False

    row, col = position_in_play
    square = new_game_state["board_state"][row][col]
    piece = next((p for p in square or [] if "neutral" not in p.get("type", "")), None)

    if not piece:
        return False

    side = piece["type"].split("_")[0]
    moves_info = moves.get_moves(old_game_state, new_game_state, position_in_play, piece)

    for possible_move in moves_info["possible_moves"]:
        simulated_state = copy.deepcopy(new_game_state)
        simulated_state["board_state"][possible_move[0]][possible_move[1]] = simulated_state["board_state"][row][col]
        simulated_state["board_state"][row][col] = None
        manage_check_status(copy.deepcopy(new_game_state), simulated_state)
        if not simulated_state["check"][side]:
            return True

    for possible_capture in moves_info["possible_captures"]:
        simulated_state = copy.deepcopy(new_game_state)
        simulated_state["board_state"][possible_capture[0][0]][possible_capture[0][1]] = simulated_state["board_state"][row][col]
        simulated_state["board_state"][possible_capture[1][0]][possible_capture[1][1]] = None
        simulated_state["board_state"][row][col] = None
        manage_check_status(copy.deepcopy(new_game_state), simulated_state)
        if not simulated_state["check"][side]:
            return True

    return False
