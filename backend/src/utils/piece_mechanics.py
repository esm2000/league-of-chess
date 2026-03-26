"""Piece-specific effects: bishop energize/debuffs, queen stuns, and adjacent captures."""

import traceback

from src.log import logger
from src.types import GameState, MoveResult, MovedPiece, Position
import src.moves as moves
from .check_checkmate import trim_king_moves


def apply_bishop_energize_stacks_and_bishop_debuffs(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece]) -> None:
    """Award energize stacks to moved bishops and apply bishop_debuff to threatened pieces."""
    positions_with_bishop_debuffs_applied = []
    for i, moved_piece in enumerate(moved_pieces):
        if "bishop" in moved_piece["piece"]["type"] and moved_piece["previous_position"][0] is not None and moved_piece["current_position"][0] is not None:
            distance_moved = abs(moved_piece["previous_position"][0] - moved_piece["current_position"][0])
            energize_stacks_to_add = 5 * distance_moved
            moves_info = moves.get_moves_for_bishop(
                curr_game_state=old_game_state,
                prev_game_state=old_game_state.get("previous_state"),
                curr_position=moved_piece["previous_position"]
            )
            for j, piece in enumerate(moved_pieces):
                if i == j or piece["current_position"][0] is not None:
                    continue
                if any(capture_positions[0] == moved_piece["current_position"] and capture_positions[1] == piece["previous_position"] for capture_positions in moves_info["possible_captures"]):
                    energize_stacks_to_add += 10
            for piece in new_game_state["board_state"][moved_piece["current_position"][0]][moved_piece["current_position"][1]]:
                if "bishop" in piece["type"]:
                    if "energize_stacks" not in piece:
                        piece["energize_stacks"] = energize_stacks_to_add
                    else:
                        piece["energize_stacks"] += energize_stacks_to_add

                    if piece.get("energize_stacks", 0) > 100:
                        piece["energize_stacks"] = 100

            future_moves_info = moves.get_moves_for_bishop(
                curr_game_state=new_game_state,
                prev_game_state=old_game_state,
                curr_position=moved_piece["current_position"]
            )
            opposing_side = "white" if moved_piece["side"] == "black" else "black"
            if future_moves_info["possible_captures"]:
                for possible_capture_info in future_moves_info["possible_captures"]:
                    position_of_piece_in_danger = possible_capture_info[1]
                    if position_of_piece_in_danger in positions_with_bishop_debuffs_applied:
                        continue
                    positions_with_bishop_debuffs_applied.append(position_of_piece_in_danger)
                    if not new_game_state["board_state"][position_of_piece_in_danger[0]][position_of_piece_in_danger[1]]:
                        continue
                    for piece in new_game_state["board_state"][position_of_piece_in_danger[0]][position_of_piece_in_danger[1]]:
                        if opposing_side not in piece.get('type'):
                            continue
                        if "bishop_debuff" not in piece:
                            piece["bishop_debuff"] = 1
                        elif piece["bishop_debuff"] < 3:
                            piece["bishop_debuff"] += 1


def apply_queen_stun(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece]) -> None:
    """Stun all adjacent enemy pieces (except kings) when a queen moves without capturing."""
    for i, moved_piece in enumerate(moved_pieces):
        if "queen" in moved_piece["piece"]["type"] and moved_piece["previous_position"][0] is not None and moved_piece["current_position"][0] is not None:
            queen_side = moved_piece["side"]
            moves_info = moves.get_moves_for_queen(
                curr_game_state=old_game_state,
                prev_game_state=old_game_state.get("previous_state"),
                curr_position=moved_piece["previous_position"]
            )
            can_stun = True
            for j, piece in enumerate(moved_pieces):
                if i == j or piece["current_position"][0] is not None:
                    continue
                if any(capture_positions[0] == moved_piece["current_position"] and capture_positions[1] == piece["previous_position"] for capture_positions in moves_info["possible_captures"]):
                    can_stun = False
                    break
            if can_stun:
                directions = [[0, 1], [1, 0], [0, -1], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]]
                for direction in directions:
                    row, col = moved_piece["current_position"][0] + direction[0], moved_piece["current_position"][1] + direction[1]
                    if row < 0 or col < 0 or row > 7 or col > 7:
                        continue
                    square = new_game_state["board_state"][row][col]
                    if square:
                        for piece in square:
                            side = piece["type"].split("_")[0]
                            if queen_side != side and "king" not in piece["type"] and side != "neutral":
                                piece["is_stunned"] = True
                                piece["turn_stunned_for"] = old_game_state["turn_count"] + 1


def facilitate_adjacent_capture(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece]) -> None:
    """Execute adjacent captures (bishop energize, marked-for-death) by removing captured pieces.

    Mutates:
        new_game_state: Removes captured pieces from board, adds to captured_pieces.
        moved_pieces: Appends entries for newly captured pieces.
    """
    moved_pieces_pointer = 0
    while moved_pieces_pointer < len(moved_pieces):
        moved_piece = moved_pieces[moved_pieces_pointer]
        if moved_piece["previous_position"][0] is None or \
        moved_piece["current_position"][1] is None or \
        moved_piece["side"] == "neutral":
            moved_pieces_pointer += 1
            continue

        try:
            moves_info = moves.get_moves(old_game_state.get("previous_state"), old_game_state, moved_piece["previous_position"], moved_piece["piece"])
            if "king" in moved_piece["piece"].get("type"):
                moves_info = trim_king_moves(moves_info, old_game_state.get("previous_state"), old_game_state, moved_piece["side"])
        except Exception as e:
            logger.error(f"Unable to determine move for {moved_piece['piece']} due to: {traceback.format_exc()}")
            moved_pieces_pointer += 1
            continue

        possible_captures = moves_info["possible_captures"]
        for possible_capture in possible_captures:
            if possible_capture[0] != moved_piece["current_position"]:
                continue
            adajacent_pieces_to_capture_found = True
            for mp in moved_pieces:
                if mp["current_position"][0] is None and mp["previous_position"] == possible_capture[1]:
                    adajacent_pieces_to_capture_found = False
            if adajacent_pieces_to_capture_found:
                square = new_game_state["board_state"][possible_capture[1][0]][possible_capture[1][1]]
                piece_pointer = 0
                while piece_pointer < len(square):
                    piece = square[piece_pointer]
                    if (moved_piece["side"] == "white" and "black" in piece["type"]) or \
                    (moved_piece["side"] == "black" and "white" in piece["type"]) or \
                    "neutral" in piece["type"] and piece["health"] == 1:
                        if "health" in piece:
                            piece["health"] = 0
                        square.pop(piece_pointer)
                        if not square:
                            new_game_state["board_state"][possible_capture[1][0]][possible_capture[1][1]] = None
                        moved_pieces.append({
                            "piece": piece,
                            "side": piece["type"].split("_")[0],
                            "previous_position": possible_capture[1],
                            "current_position": [None, None]
                        })
                        new_game_state["captured_pieces"][moved_piece["side"]].append(piece["type"])
                    piece_pointer += 1
        moved_pieces_pointer += 1


def enable_adjacent_bishop_captures(curr_game_state: GameState, side: str, possible_moves_dict: MoveResult) -> MoveResult:
    """Add captures for enemy bishops adjacent to any of the piece's possible move squares."""
    adjacent_squares = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]
    opposing_side = "white" if side == "black" else "black"
    for possible_move in possible_moves_dict["possible_moves"]:
        for adjacent_square in adjacent_squares:
            potential_bishop_square = [possible_move[0] + adjacent_square[0], possible_move[1] + adjacent_square[1]]
            if potential_bishop_square[0] < 0 or potential_bishop_square[0] > 7 or potential_bishop_square[1] < 0 or potential_bishop_square[1] > 7:
                continue
            if curr_game_state["board_state"][potential_bishop_square[0]][potential_bishop_square[1]] and \
            any(piece.get("type", "") == f"{opposing_side}_bishop" for piece in curr_game_state["board_state"][potential_bishop_square[0]][potential_bishop_square[1]]):
                possible_moves_dict["possible_captures"].append([possible_move, potential_bishop_square])
    return possible_moves_dict


def handle_pieces_with_full_bishop_debuff_stacks(
    old_game_state: GameState,
    new_game_state: GameState,
    moved_pieces: list[MovedPiece],
    is_valid_game_state: bool,
    capture_positions: list[list[Position]]
) -> tuple[bool, bool]:
    """Handle bishop 3-stack debuff resolution: spare, capture, or invalidate.

    Returns:
        (is_valid_game_state, should_increment_turn_count)

    Mutates:
        new_game_state: May clear position_in_play, update energize stacks.
        capture_positions: May append bishop debuff capture positions.
    """

    def get_pieces_with_three_bishop_stacks_from_state(game_state: GameState) -> list[dict]:
        output = []
        for i, row in enumerate(game_state["board_state"]):
            for j, square in enumerate(row):
                if square:
                    for piece in square:
                        if piece.get("bishop_debuff", 0) == 3:
                            output.append({
                                "piece": piece.copy(), "position": [i, j]
                            })
        return output


    def did_piece_get_full_bishop_debuffs_this_turn(old_game_state: GameState, new_piece_info: dict) -> bool:
        row = new_piece_info["position"][0]
        col = new_piece_info["position"][1]
        square = old_game_state["board_state"][row][col]
        if not square:
            return False
        for piece in square:
            if piece["type"] == new_piece_info["piece"]["type"] and \
            new_piece_info["piece"].get("bishop_debuff", 0) == 3 and \
            piece.get("bishop_debuff", 0) == 2:
                return True
        return False

    def did_piece_get_spared_this_turn_from_special_bishop_capture(new_game_state: GameState, old_piece_info: dict) -> bool:
        row = old_piece_info["position"][0]
        col = old_piece_info["position"][1]
        square = new_game_state["board_state"][row][col]
        if not square:
            return False

        for piece in square:
            if piece["type"] == old_piece_info["piece"]["type"] and piece.get("bishop_debuff", 0) == 0:
                return True
        return False

    def more_than_one_side_has_pieces_captured(old_game_state: GameState, new_game_state: GameState) -> bool:
        return len(old_game_state["captured_pieces"]["white"]) != len(new_game_state["captured_pieces"]["white"]) and \
        len(old_game_state["captured_pieces"]["black"]) != len(new_game_state["captured_pieces"]["black"])

    def have_pieces_have_been_captured(old_game_state: GameState, new_game_state: GameState) -> bool:
        return len(old_game_state["captured_pieces"]["white"]) != len(new_game_state["captured_pieces"]["white"]) or \
        len(old_game_state["captured_pieces"]["black"]) != len(new_game_state["captured_pieces"]["black"])

    should_increment_turn_count = True
    pieces_with_three_bishop_stacks_this_turn = get_pieces_with_three_bishop_stacks_from_state(new_game_state)
    sides_from_with_three_bishop_stacks_this_turn = [piece_info["piece"]["type"].split("_")[0] for piece_info in pieces_with_three_bishop_stacks_this_turn]
    pieces_with_three_bishop_stacks_last_turn = get_pieces_with_three_bishop_stacks_from_state(old_game_state)

    if pieces_with_three_bishop_stacks_this_turn:
        new_game_state["position_in_play"] = [None, None]
        # scenario 0 - catch all - more than one side has 3 bishop debuffs
        #            - invalidate game
    if "white" in sides_from_with_three_bishop_stacks_this_turn and \
        "black" in sides_from_with_three_bishop_stacks_this_turn:
        logger.error("More than one side has full bishop debuff stacks")
        is_valid_game_state = False
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: more than one side has full bishop debuff stacks")
        # scenario 1 - (can be any) pieces on the board have third bishop debuff and did not have all three last turn
        #            - or they had all three last turn but another piece with a third bishop debuff was dealt with instead
        #            - turn count is not being incremented
    elif any([did_piece_get_full_bishop_debuffs_this_turn(old_game_state, piece_info) for piece_info in pieces_with_three_bishop_stacks_this_turn]):
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: piece got full bishop debuffs this turn")
        # scenario 2 - illegal move is attempted instead of dealing with bishop debuffs
        #            - search through moved pieces and invalidate game state if any pieces moved (valid old position and new position) if there's any third bishop buff active in old_game_state
    elif pieces_with_three_bishop_stacks_last_turn and \
    len([moved_piece for moved_piece in moved_pieces if moved_piece["previous_position"][0] is not None and moved_piece["current_position"][0] is not None]) > 0:
        logger.error("Illegal move was attempted instead of dealing with full bishop debuff stacks")
        is_valid_game_state = False
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: illegal move instead of dealing with bishop debuffs")
        # scenario 3 - a piece that had third bishop debuff in the previous game state has no debuffs present in the current game state
        #            - player spared piece
        #            - turn count is being incremented
        #            - (technically allow sparing of multiple pieces since this isn't game breaking behavior)
    elif pieces_with_three_bishop_stacks_last_turn and \
    all([did_piece_get_spared_this_turn_from_special_bishop_capture(new_game_state, piece_info) for piece_info in pieces_with_three_bishop_stacks_last_turn]):
        # Spare resolution has no moved_pieces, so increment_turn_count() in the
        # pipeline would skip. Increment directly and tell pipeline not to re-increment.
        new_game_state["turn_count"] += 1
        should_increment_turn_count = False
        # scenario 4 - more than one piece has been captured
    elif (pieces_with_three_bishop_stacks_this_turn or pieces_with_three_bishop_stacks_last_turn) and \
    more_than_one_side_has_pieces_captured(old_game_state, new_game_state):
        logger.error("More than one side has pieces captured after dealing with full bishop debuff stacks")
        is_valid_game_state = False
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: more than one side has pieces captured after bishop debuffs")
        # scenario 5 - there is a piece in the moved_pieces array that shows that a piece was captured (via bishop debuffs)
        #            - player captured piece and game has to ensure that state is not invalidated later on
        #              by appending captured piece's position to capture_positions
        #            - turn count is being incremented only if there are no other pieces to spare or capture
    elif pieces_with_three_bishop_stacks_last_turn and \
    have_pieces_have_been_captured(old_game_state, new_game_state):
        if not new_game_state["bishop_special_captures"]:
            logger.error("Bishop special capture positions not properly marked even though piece has been captured")
            is_valid_game_state = False
            should_increment_turn_count = False
            logger.debug("Not incrementing turn count: bishop special captures not properly marked")
        else:
            captured_side = new_game_state["bishop_special_captures"][0]["type"].split("_")[0]
            opposite_side = "white" if captured_side == "black" else "black"
            is_found = False
            for row in range(0, len(new_game_state["board_state"])):
                for col in range(0, len(new_game_state["board_state"])):
                    if is_found:
                        break
                    new_square = new_game_state["board_state"][row][col]

                    if not new_square:
                        continue

                    for piece in new_square:
                        if piece.get("type", "") == f"{opposite_side}_bishop":
                            moves_info = moves.get_moves_for_bishop(old_game_state, old_game_state.get("previous_state"), [row, col])
                            if new_game_state["bishop_special_captures"][0]["position"] in moves_info["possible_moves"] or \
                            new_game_state["bishop_special_captures"][0]["position"] in [possible_capture[1] for possible_capture in moves_info["possible_captures"]]:
                                new_capture_position = [[row, col], new_game_state["bishop_special_captures"][0]["position"]]
                                is_found = True
            should_increment_turn_count = len(pieces_with_three_bishop_stacks_this_turn) == 0
            if not is_found:
                is_valid_game_state = False
                logger.error(f'Unable to find a {opposite_side} bishop that could capture {new_game_state["bishop_special_captures"][0]["type"]}')
            else:
                capture_positions.append(new_capture_position)
                # find bishop responsible and apply energize stacks in this scenario
                for entry in new_game_state["latest_movement"]["record"]:
                    if entry["piece"]["type"] == f"{opposite_side}_bishop":
                        try:
                            moves_info = moves.get_moves_for_bishop(
                                curr_game_state=old_game_state,
                                prev_game_state=old_game_state.get("previous_state"),
                                curr_position=entry["current_position"]
                            )

                            if new_capture_position[1] not in [possible_capture[1] for possible_capture in moves_info["possible_captures"]]:
                                raise Exception("Last moved bishop cannot capture the captured piece")
                        except Exception as e:
                            logger.error(f'Unable to find a {opposite_side} bishop to give energize stacks for bishop debuff capture at {entry["current_position"]}: {e}')
                            is_valid_game_state = False
                        else:
                            for piece in new_game_state["board_state"][entry["current_position"][0]][entry["current_position"][1]]:
                                if "energize_stacks" not in piece:
                                    piece["energize_stacks"] = 10
                                else:
                                    piece["energize_stacks"] += 10

                                if piece.get("energize_stacks", 0) > 100:
                                    piece["energize_stacks"] = 100

    return is_valid_game_state, should_increment_turn_count

def clean_bishop_special_captures(new_game_state: GameState) -> None:
    """Clear bishop_special_captures for the next turn."""
    new_game_state["bishop_special_captures"] = []
