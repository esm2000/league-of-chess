"""Queen turn-reset logic: kill/assist detection and position-in-play assignment."""

from src.log import logger
from src.types import GameState, MovedPiece
import src.moves as moves


def reset_queen_turn_on_kill_or_assist(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], should_increment_turn_count: bool) -> bool:
    """Grant queen an extra turn if she killed or assisted a kill. Returns updated should_increment_turn_count."""
    moving_side = "white" if not bool(old_game_state["turn_count"] % 2) else "black"
    for i in range(len(old_game_state["board_state"])):
        row = old_game_state["board_state"][i]
        for j in range(len(row)):
            square = row[j] or []
            for piece in square:
                if piece["type"] == f"{moving_side}_queen":
                    queen_possible_moves_and_captures = moves.get_moves_for_queen(
                        curr_game_state=old_game_state,
                        prev_game_state=old_game_state.get("previous_state"),
                        curr_position=[i, j]
                    )

                    enemy_side = "black" if moving_side == "white" else "white"
                    queen_moved_to = None
                    for mp in moved_pieces:
                        if mp["piece"].get("type") == f"{moving_side}_queen" and mp["current_position"][0] is not None:
                            queen_moved_to = mp["current_position"]

                    for moved_piece in moved_pieces:
                        if moved_piece["current_position"][0] is None and \
                        moved_piece["side"] == enemy_side and \
                        (
                            moved_piece["previous_position"] in queen_possible_moves_and_captures["possible_moves"] or \
                            moved_piece["previous_position"] in [capture_info[1] for capture_info in queen_possible_moves_and_captures["possible_captures"]]
                        ):
                            is_kill = queen_moved_to == moved_piece["previous_position"]
                            new_game_state["queen_reset"] = True
                            new_game_state["queen_reset_type"] = "kill" if is_kill else "assist"
                            should_increment_turn_count = False
                            logger.debug(f"Not incrementing turn count: queen reset triggered on {'kill' if is_kill else 'assist'}")
    return should_increment_turn_count


def set_queen_as_position_in_play(old_game_state: GameState, new_game_state: GameState) -> bool:
    """Set position_in_play to the queen's location for the moving side. Returns True if queen not found."""
    moving_side = "white" if not bool(old_game_state["turn_count"] % 2) else "black"
    for i in range(len(new_game_state["board_state"])):
        row = new_game_state["board_state"][i]
        for j in range(len(row)):
            square = row[j] or []
            for piece in square:
                if piece["type"] == f"{moving_side}_queen":
                    new_game_state["position_in_play"] = [i, j]
                    return False
    return True



def verify_queen_reset_turn_is_valid(
    old_game_state: GameState,
    new_game_state: GameState,
    moved_pieces: list[MovedPiece],
    is_valid_game_state: bool
) -> bool:
    """Validate that only the queen moved during a queen reset turn."""
    moving_side = "white" if not bool(old_game_state["turn_count"] % 2) else "black"
    # check for proper queen moving or that proper queen is set as the position in play
    proper_queen_found = False
    is_proper_queen_in_play = False

    for moved_piece in moved_pieces:
        if moved_piece["side"] == moving_side and \
        moved_piece["previous_position"][0] is not None and \
        moved_piece["current_position"][0] is not None:
            piece_type = moved_piece["piece"].get("type")
            if "queen" in piece_type:
                proper_queen_found = True
            else:
                is_valid_game_state = False
                logger.error(f"A non-queen piece moved for {moving_side} instead of the queen using its turn reset")

    if new_game_state["position_in_play"][0] is not None:
        position_in_play = new_game_state["position_in_play"]
        square_in_play = new_game_state["board_state"][position_in_play[0]][position_in_play[1]] or []
        is_proper_queen_in_play = any(f"{moving_side}_queen" == piece.get("type", "") for piece in square_in_play)

    if not proper_queen_found and not is_proper_queen_in_play:
        is_valid_game_state = False
        logger.error(f"{moving_side}'s queen is not in play and has not moved despite its turn reset")

    return is_valid_game_state
