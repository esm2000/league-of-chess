"""FastAPI route definitions for game CRUD, state updates, and move queries."""

from bson.objectid import ObjectId
import copy
import datetime
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Extra
from typing import Union

from mocks.starting_game import starting_game
# prevents circular import
import src.moves as moves
from src.database import mongo_client
from src.log import logger
import src.utils as utils
from src.utils.game_update_pipeline import (
    prepare_game_update,
    apply_special_piece_effects,
    manage_turn_progression,
    validate_moves_and_pieces,
    handle_pawn_exchanges,
    handle_captures_and_combat,
    update_game_metrics,
    handle_endgame_conditions,
    finalize_game_state,
    unmark_all_pieces_marked_for_death
)

router = APIRouter(prefix="/api")


class GameStateRequest(BaseModel, extra=Extra.allow):
    turn_count: int
    position_in_play: list
    board_state: list
    possible_moves: list
    possible_captures: list
    captured_pieces: dict
    sword_in_the_stone_position: Union[list, None]
    capture_point_advantage: Union[list, None]
    black_defeat: bool
    white_defeat: bool
    gold_count: dict
    bishop_special_captures: list
    latest_movement: dict
    queen_reset: bool
    neutral_attack_log: dict
    check: dict
    castle_log: dict
    neutral_buff_log: dict
    version: int = 0


@router.post("/game", status_code=201)
def create_game() -> dict:
    """Create a new game with the starting board state and persist to MongoDB."""
    game_state = copy.deepcopy(starting_game)
    game_database = mongo_client["game_db"]
    game_database["games"].insert_one(game_state)
    game_state["id"] = str(game_state.pop("_id"))
    return game_state


@router.get("/game/{id}", status_code=200)
def retrieve_game_state(id: str, response: Response) -> dict:
    """Fetch a game state from MongoDB by ID."""
    game_database = mongo_client["game_db"]
    game_state = game_database["games"].find_one({"_id": ObjectId(id)})
    if not game_state:
        response.status_code = 404
        return {"message": "Game not found"}
    game_state["id"] = str(game_state.pop("_id"))
    return game_state


@router.delete("/game/{id}")
def delete_game(id: str) -> dict:
    """Delete a game from MongoDB by ID."""
    query = {"_id": ObjectId(id)}
    game_database = mongo_client["game_db"]
    game_database["games"].delete_one(query)
    return {"message": "Success"}


@router.put("/game/{id}", status_code=200)
def update_game_state(id: str, state: GameStateRequest, response: Response, player: bool = True) -> dict:
    """Validate and apply a full game state update (the main turn pipeline)."""
    # Prepare initial game state
    old_game_state, new_game_state, moved_pieces = prepare_game_update(id, state, retrieve_game_state)
    
    # Early return if game has ended
    if new_game_state is None:
        return old_game_state
    
    # Initialize validation state
    capture_positions = []
    
    # Apply special piece effects and validate
    is_valid_game_state = apply_special_piece_effects(old_game_state, new_game_state, moved_pieces)
    
    # Manage turn progression
    is_valid_game_state, should_increment_turn_count = manage_turn_progression(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, capture_positions
    )
    
    # Validate moves and pieces
    is_valid_game_state, gold_spent = validate_moves_and_pieces(
        old_game_state, new_game_state, moved_pieces, capture_positions, is_valid_game_state
    )

    # if game state is still valid while marked for death pieces are present that is indicative of 
    # one piece being chosen for sacrifice (validate_moves_and_pieces), so unmark all pieces
    if is_valid_game_state:
        unmark_all_pieces_marked_for_death(new_game_state)
    
    # Handle pawn exchanges
    is_pawn_exchange_required_this_turn, is_pawn_exchange_possibly_being_carried_out = handle_pawn_exchanges(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state
    )
    
    # Handle captures and combat
    is_valid_game_state = handle_captures_and_combat(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, 
        capture_positions, is_pawn_exchange_possibly_being_carried_out
    )
    
    # Update game metrics
    update_game_metrics(old_game_state, new_game_state, moved_pieces, gold_spent)
    
    # Handle endgame conditions
    is_valid_game_state = handle_endgame_conditions(
        old_game_state, new_game_state, moved_pieces, is_valid_game_state, should_increment_turn_count
    )

    # Finalize game state
    finalize_game_state(old_game_state, new_game_state, moved_pieces, player, 
                       is_pawn_exchange_required_this_turn, mongo_client, id)
    
    return retrieve_game_state(id, response)


def update_game_state_no_restrictions(id: str, state: GameStateRequest, response: Response) -> dict:
    """Overwrite a game state without validation (testing only, not exposed via API)."""
    new_game_state = dict(state)
    new_game_state["last_updated"] = datetime.datetime.now()
    query = {"_id": ObjectId(id)}
    new_values = {"$set": new_game_state}
    game_database = mongo_client["game_db"]
    game_database["games"].update_one(query, new_values)
    return retrieve_game_state(id, response)