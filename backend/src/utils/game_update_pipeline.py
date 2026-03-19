"""Turn orchestration pipeline: validation, effects, progression, and finalization."""

from __future__ import annotations

import datetime
from typing import Callable, TYPE_CHECKING

from fastapi import HTTPException, Response
from pymongo.mongo_client import MongoClient

from src.log import logger
from src.types import GameState, GoldSpent, MovedPiece, PawnExchangeStatus, Position
import src.utils as utils

if TYPE_CHECKING:
    from src.api import GameStateRequest


def prepare_game_update(id: str, state: GameStateRequest, retrieve_game_state_func: Callable) -> tuple[GameState, GameState | None, list[MovedPiece] | None]:
    """Load old state, compute moved pieces. Returns (old, None, None) if game already ended."""
    new_game_state = dict(state)
    old_game_state = retrieve_game_state_func(id, Response())
    
    # prevent updates to game once game has ended
    if old_game_state["black_defeat"] or old_game_state["white_defeat"]:
        logger.info(f"Game update terminated early - Game already ended. black_defeat: {old_game_state['black_defeat']}, white_defeat: {old_game_state['white_defeat']}")
        return old_game_state, None, None
    
    # determine moved pieces
    try:
        moved_pieces = utils.determine_pieces_that_have_moved(
            new_game_state["board_state"], old_game_state["board_state"]
        )
    except Exception as e:
        logger.error(f"Unable to determine pieces that have moved: {e}")
        raise HTTPException(status_code=400, detail=utils.INVALID_GAME_STATE_ERROR_MESSAGE)
    
    return old_game_state, new_game_state, moved_pieces


def apply_special_piece_effects(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece]) -> bool:
    """Apply queen reset validation, adjacent captures, bishop energize, and queen stun."""
    is_valid_game_state = True
    
    # Queen reset validation
    if new_game_state.get("queen_reset"):
        is_valid_game_state = utils.verify_queen_reset_turn_is_valid(
            old_game_state, new_game_state, moved_pieces, is_valid_game_state
        )
    
    # Apply piece effects
    utils.facilitate_adjacent_capture(old_game_state, new_game_state, moved_pieces)
    utils.apply_bishop_energize_stacks_and_bishop_debuffs(old_game_state, new_game_state, moved_pieces)
    utils.apply_queen_stun(old_game_state, new_game_state, moved_pieces)
    
    return is_valid_game_state


def manage_turn_progression(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], is_valid_game_state: bool, capture_positions: list[list[Position]]) -> tuple[bool, bool]:
    """Handle bishop debuff, position-in-play, marked-for-death, queen reset, and turn increment."""
    should_increment_turn_count = True
    
    # Bishop debuff stack handling
    is_valid_game_state, should_increment_turn_count = utils.handle_pieces_with_full_bishop_debuff_stacks(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, capture_positions
    )
    
    # position in play selection logic
    if utils.was_a_new_position_in_play_selected(moved_pieces, old_game_state, new_game_state) and new_game_state["position_in_play"][0] is not None and new_game_state["position_in_play"][1] is not None:
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: new position in play selected")
        is_valid_game_state = utils.does_position_in_play_match_turn(old_game_state, new_game_state) and is_valid_game_state
    
    # if there are any non-stunned pieces marked for death on the board, don't increment turn count
    # (board from previous turn is scanned, since it's possible that only one piece is marked for death and that piece could be surrendered this turn)
    has_active_marked_for_death = False
    for row in range(len(old_game_state["board_state"])):
        for col in range(len(old_game_state["board_state"][row])):
            for piece in old_game_state["board_state"][row][col] or []:
                if piece.get("marked_for_death", False) and not piece.get("is_stunned", False):
                    has_active_marked_for_death = True

    if has_active_marked_for_death:
        should_increment_turn_count = False
        logger.debug("Not incrementing turn count: piece marked for death found on board")

    # queen turn logic
    if new_game_state["queen_reset"] and should_increment_turn_count:
        new_game_state["queen_reset"] = False
    else:
        should_increment_turn_count = utils.reset_queen_turn_on_kill_or_assist(
            old_game_state, new_game_state, moved_pieces, should_increment_turn_count
        )
    
    # clean and increment
    utils.clean_possible_moves_and_possible_captures(new_game_state)
    if should_increment_turn_count:
        logger.debug(f"{should_increment_turn_count=}")
        utils.increment_turn_count(old_game_state, new_game_state, moved_pieces, 1)
    utils.prevent_client_side_updates_to_graveyard(old_game_state, new_game_state)
    
    return is_valid_game_state, should_increment_turn_count


def validate_moves_and_pieces(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], capture_positions: list[list[Position]], is_valid_game_state: bool) -> tuple[bool, GoldSpent]:
    """Run all move/piece validators and return (is_valid, gold_spent)."""
    # Core move validation
    is_valid_game_state = utils.check_to_see_if_more_than_one_piece_has_moved(
        old_game_state,
        new_game_state,
        moved_pieces,
        capture_positions,
        is_valid_game_state
    )

    # Invalidate game state if pieces are marked for death in the old game state and the current turn's side
    # did not choose any of them to die
    is_valid_game_state = utils.invalidate_game_if_no_marked_for_death_pieces_have_been_selected(
        old_game_state,
        new_game_state,
        is_valid_game_state
    )
    
    # Update castle log and validate gold
    utils.update_castle_log(new_game_state, moved_pieces)
    gold_spent = utils.get_gold_spent(moved_pieces)
    
    # Move count validation
    move_count_for_white, move_count_for_black = utils.get_move_counts(moved_pieces)
    is_valid_game_state = utils.invalidate_game_if_more_than_one_side_moved(
        move_count_for_white, move_count_for_black, is_valid_game_state
    )
    
    # Other validations
    is_valid_game_state = utils.invalidate_game_if_stunned_piece_moves(moved_pieces, is_valid_game_state)
    is_valid_game_state = utils.invalidate_game_if_wrong_side_moves(
        moved_pieces, is_valid_game_state, old_game_state["turn_count"]
    )
    is_valid_game_state = utils.invalidate_game_if_too_much_gold_is_spent(
        old_game_state, gold_spent, is_valid_game_state
    )
    is_valid_game_state = utils.invalidate_game_if_monster_has_moved(is_valid_game_state, moved_pieces)
    
    utils.cleanse_stunned_pieces(new_game_state)
    
    return is_valid_game_state, gold_spent


def handle_pawn_exchanges(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], is_valid_game_state: bool) -> tuple[bool, PawnExchangeStatus]:
    """Check for and process pawn promotion exchanges. Returns (is_required, exchange_status)."""
    is_pawn_exchange_required_this_turn, is_valid_game_state = utils.check_if_pawn_exchange_is_required(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state
    )
    is_pawn_exchange_possibly_being_carried_out = utils.check_if_pawn_exchange_is_possibly_being_carried_out(
        old_game_state, new_game_state, moved_pieces
    )
    
    should_increment_turn_count_for_pawn_exchange = utils.should_turn_count_be_incremented_for_pawn_exchange(
        old_game_state, is_pawn_exchange_possibly_being_carried_out
    )
    
    if should_increment_turn_count_for_pawn_exchange:
        utils.increment_turn_count(old_game_state, new_game_state, moved_pieces, 1)
    
    if not should_increment_turn_count_for_pawn_exchange and is_pawn_exchange_required_this_turn:
        utils.reset_turn_count(old_game_state, new_game_state)
    
    return is_pawn_exchange_required_this_turn, is_pawn_exchange_possibly_being_carried_out


def handle_captures_and_combat(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], is_valid_game_state: bool,
                               capture_positions: list[list[Position]], is_pawn_exchange_possibly_being_carried_out: PawnExchangeStatus) -> bool:
    """Validate captures, damage monsters, and apply neutral monster buffs."""
    # Check for disappearing pieces
    is_valid_game_state = utils.check_for_disappearing_pieces(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, 
        capture_positions, is_pawn_exchange_possibly_being_carried_out
    )
    
    # Clean bishop special captures and damage monsters
    utils.clean_bishop_special_captures(new_game_state)
    utils.damage_neutral_monsters(new_game_state, moved_pieces, capture_positions)
    
    # Validate captures
    is_valid_game_state = utils.invalidate_game_when_unexplained_pieces_are_in_captured_pieces_array(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, is_pawn_exchange_possibly_being_carried_out
    )
    
    # Neutral monster validation
    if utils.get_neutral_monster_slain_positions(moved_pieces) and not utils.is_neutral_monster_killed(moved_pieces):
        logger.error("A neutral monster disappeared from board without being captured")
        is_valid_game_state = False
    
    # Conditionally grants neutral monster buffs
    is_valid_game_state = utils.handle_neutral_monster_buffs(moved_pieces, capture_positions, new_game_state, is_valid_game_state)

    # King capture validation
    if utils.is_invalid_king_capture(moved_pieces):
        logger.error("A king has been captured or has disappeared from board")
        is_valid_game_state = False
    
    return is_valid_game_state


def update_game_metrics(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], gold_spent: GoldSpent) -> None:
    """Update gold, capture advantage, pawn buffs, monster attacks, and spawns."""
    utils.update_gold_count(old_game_state, new_game_state, gold_spent)
    utils.update_capture_point_advantage(new_game_state)
    utils.reassign_pawn_buffs(new_game_state)
    
    # Neutral monster attacks
    if len(moved_pieces) > 0:
        utils.carry_out_neutral_monster_attacks(new_game_state)
    
    utils.spawn_neutral_monsters(new_game_state)


def handle_endgame_conditions(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], is_valid_game_state: bool, should_increment_turn_count: bool) -> bool:
    """Check/checkmate detection, marked-for-death application, stun skip, and monster healing."""
    # Check and checkmate logic
    utils.manage_check_status(old_game_state, new_game_state)

    # Validate check escape
    is_valid_game_state = utils.invalidate_game_if_player_moves_and_is_in_check(
        is_valid_game_state, old_game_state, new_game_state, moved_pieces
    )

    if not is_valid_game_state:
        raise HTTPException(status_code=400, detail=utils.INVALID_GAME_STATE_ERROR_MESSAGE)

    # if any of the piece(s) that moved this turn have five dragon buff stacks mark all non-king adjacent pieces for death
    # but only do this is new_game_state's turn count is greater than old_game_state's turn count or when queen_reset is True for new_game_state but False for old_game_state
    have_any_pieces_been_marked_for_death = False
    if new_game_state["turn_count"] > old_game_state["turn_count"] or (new_game_state["queen_reset"] and not old_game_state["queen_reset"]):
        for moved_piece in [mp for mp in moved_pieces if mp["previous_position"][0] is not None and mp["current_position"][0] is not None]:
            if moved_piece["piece"].get("dragon_buff", 0) < 5:
                continue

            deltas = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]]
            opposite_side = "white" if moved_piece["side"] == "black" else "black"

            for delta in deltas:
                position = [moved_piece["current_position"][0] + delta[0], moved_piece["current_position"][1] + delta[1]]
                if position[0] < 0 or position[0] > 7 or position[1] < 0 or position[1] > 7:
                    continue
                
                square = new_game_state["board_state"][position[0]][position[1]] or []
                for piece in square:
                    if opposite_side in piece.get("type") and "king" not in piece.get("type"):
                        piece["marked_for_death"] = True
                        have_any_pieces_been_marked_for_death = True

    # Checkmate check runs after marks are applied so that marked-for-death surrenders
    # (which could open an escape square for the king) are considered before declaring checkmate.
    utils.end_game_on_checkmate(old_game_state, new_game_state)

    # handle stunned piece special case if pieces have not been marked for death this turn
    if should_increment_turn_count and utils.are_all_non_king_pieces_stunned(new_game_state) and not utils.can_king_move(old_game_state, new_game_state) and not have_any_pieces_been_marked_for_death:
        utils.increment_turn_count(old_game_state, new_game_state, moved_pieces, 2)

    # if there are pieces marked for death in old game state and none marked for death this turn but all of the current player's pieces are stunned increment turn count by 1
    # (this is different from the current are_all_non_king_pieces_stunned() because the side that is supposed to be moving this turn should be assessed
    have_any_pieces_been_marked_for_death_in_past = False
    for row in range(len(old_game_state["board_state"])):
        for col in range(len(old_game_state["board_state"][row])):
            square = old_game_state["board_state"][row][col] or []

            for piece in square:
                if piece.get("marked_for_death", False):
                    have_any_pieces_been_marked_for_death_in_past = True
    
    if have_any_pieces_been_marked_for_death_in_past \
        and not have_any_pieces_been_marked_for_death \
        and should_increment_turn_count \
        and utils.are_all_non_king_pieces_stunned(new_game_state, True) \
        and not utils.can_king_move(old_game_state, new_game_state, True) \
        and old_game_state["turn_count"] == new_game_state["turn_count"]:
        utils.increment_turn_count(old_game_state, new_game_state, moved_pieces, 1)

    # Heal monsters
    utils.heal_neutral_monsters(old_game_state, new_game_state)
    
    return is_valid_game_state


def finalize_game_state(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], player: bool, is_pawn_exchange_required_this_turn: bool, mongo_client: MongoClient, id: str) -> None:
    """Record moves, set position in play, compute legal moves, handle draws/items, and persist."""
    # Record movement
    utils.record_moved_pieces_this_turn(new_game_state, moved_pieces)

    # Position in play logic
    reset_position_in_play_queen = True
    if new_game_state["queen_reset"]:
        reset_position_in_play_queen = utils.set_queen_as_position_in_play(old_game_state, new_game_state)
    
    reset_position_in_play_king = utils.set_next_king_as_position_in_play_if_in_check(old_game_state, new_game_state)
    
    # Determine possible moves
    reset_position_in_play = reset_position_in_play_queen and reset_position_in_play_king
    utils.determine_possible_moves(old_game_state, new_game_state, moved_pieces, player, reset_position_in_play, is_pawn_exchange_required_this_turn)
    
    # Handle draws and special items
    utils.handle_draw_conditions(old_game_state, new_game_state)
    utils.spawn_sword_in_the_stone(old_game_state, new_game_state)
    utils.exhaust_sword_in_the_stone(new_game_state, moved_pieces)
    
    # Final management and persistence
    utils.manage_game_state(old_game_state, new_game_state)
    # Use the DB-authoritative version from old_game_state (not the client's
    # potentially stale version) so the optimistic concurrency check in
    # perform_game_state_update compares against the actual DB state.
    new_game_state["version"] = old_game_state.get("version", 0)
    utils.perform_game_state_update(new_game_state, mongo_client, id)

    # Log move to game_moves collection (after persistence to avoid phantom entries)
    if moved_pieces:
        move_log = {
            "game_id": id,
            "turn": new_game_state["turn_count"],
            "side": "white" if player else "black",
            "moved_pieces": [
                {
                    "piece_type": mp["piece"]["type"],
                    "from": mp["previous_position"],
                    "to": mp["current_position"]
                }
                for mp in moved_pieces
            ],
            "captured_pieces": new_game_state["captured_pieces"],
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }
        mongo_client["game_db"]["game_moves"].insert_one(move_log)


def simulate_game_update(old_game_state: GameState, new_game_state: GameState) -> GameState | None:
    """Run the update pipeline on in-memory states without DB access.

    Mirrors the full update_game_state pipeline (special effects, turn progression,
    validation, captures, metrics, endgame) but skips DB reads/writes and finalization.
    Returns the resulting game state, or None if the pipeline rejects the move.
    """
    try:
        moved_pieces = utils.determine_pieces_that_have_moved(
            new_game_state["board_state"], old_game_state["board_state"]
        )
    except Exception:
        return None

    capture_positions = []

    try:
        is_valid = apply_special_piece_effects(old_game_state, new_game_state, moved_pieces)

        is_valid, should_increment = manage_turn_progression(
            old_game_state, new_game_state, moved_pieces, is_valid, capture_positions
        )

        is_valid, gold_spent = validate_moves_and_pieces(
            old_game_state, new_game_state, moved_pieces, capture_positions, is_valid
        )

        if is_valid:
            unmark_all_pieces_marked_for_death(new_game_state)

        is_pawn_exchange_required, is_pawn_exchange_carried_out = handle_pawn_exchanges(
            old_game_state, new_game_state, moved_pieces, is_valid
        )

        is_valid = handle_captures_and_combat(
            old_game_state, new_game_state, moved_pieces, is_valid,
            capture_positions, is_pawn_exchange_carried_out
        )

        update_game_metrics(old_game_state, new_game_state, moved_pieces, gold_spent)

        is_valid = handle_endgame_conditions(
            old_game_state, new_game_state, moved_pieces, is_valid, should_increment
        )

        return new_game_state if is_valid else None
    except HTTPException:
        return None


def unmark_all_pieces_marked_for_death(new_game_state: GameState) -> None:
    """Clear marked_for_death flag on all pieces after a valid sacrifice selection."""
    for row in range(len(new_game_state["board_state"])):
        for col in range(len(new_game_state["board_state"][row])):
            square = new_game_state["board_state"][row][col] or []

            for piece in square:
                if piece.get("marked_for_death", False):
                    piece["marked_for_death"] = False
