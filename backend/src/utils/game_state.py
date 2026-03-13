"""Game state lifecycle: initialization, turn counting, persistence, and history management."""

import copy
import datetime

from bson.objectid import ObjectId
from fastapi import Response
from pymongo.mongo_client import MongoClient

import src.api as api
from mocks.empty_game import empty_game
from src.types import GameState, MovedPiece


def clear_game(game: GameState) -> GameState:
    """Reset a game to the empty state (used in integration tests)."""
    game_on_next_turn = copy.deepcopy(game)
    for key in empty_game:
        game_on_next_turn[key] = copy.deepcopy(empty_game[key])

    game_on_next_turn["previous_state"] = copy.deepcopy(game_on_next_turn)

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
    return game


def increment_turn_count(old_game_state: GameState, new_game_state: GameState, moved_pieces: list[MovedPiece], number_of_turns: int) -> None:
    """Increment turn_count if any pieces moved."""
    if len(moved_pieces) > 0:
        new_game_state["turn_count"] = old_game_state["turn_count"] + number_of_turns

def reset_turn_count(old_game_state: GameState, new_game_state: GameState) -> None:
    """Restore turn_count to its previous value."""
    new_game_state["turn_count"] = old_game_state["turn_count"]


def manage_game_state(old_game_state: GameState, new_game_state: GameState) -> None:
    """Save old state as new state's previous_state, dropping nested history to save space."""
    previous_state_of_old_game = old_game_state.get("previous_state")
    if previous_state_of_old_game:
        old_game_state.pop("previous_state")
    new_game_state["previous_state"] = old_game_state


def perform_game_state_update(new_game_state: GameState, mongo_client: MongoClient, game_id: str) -> None:
    """Persist game state to MongoDB with version increment for optimistic concurrency."""
    new_game_state["last_updated"] = datetime.datetime.now()
    new_game_state["version"] = new_game_state.get("version", 0) + 1
    query = {"_id": ObjectId(game_id)}
    new_values = {"$set": new_game_state}
    game_database = mongo_client["game_db"]
    game_database["games"].update_one(query, new_values)


def clean_possible_moves_and_possible_captures(new_game_state: GameState) -> None:
    """Clear possible_moves and possible_captures from the previous turn."""
    new_game_state["possible_moves"] = []
    new_game_state["possible_captures"] = []


def prevent_client_side_updates_to_graveyard(old_game_state: GameState, new_game_state: GameState) -> None:
    """Overwrite client-submitted graveyard with the server's authoritative copy."""
    new_game_state["graveyard"] = old_game_state["graveyard"]


def record_moved_pieces_this_turn(new_game_state: GameState, moved_pieces: list[MovedPiece]) -> None:
    """Store actual board moves (not spawns/captures) in latest_movement for bishop energize tracking."""
    def is_captured_or_spawned(moved_pieces_entry: MovedPiece) -> bool:
        return moved_pieces_entry["previous_position"][0] is None \
        or  moved_pieces_entry["current_position"][0] is None
    filtered_moved_pieces = [entry for entry in moved_pieces if not is_captured_or_spawned(entry)]

    if filtered_moved_pieces:
        new_game_state["latest_movement"] = {
            "turn_count": new_game_state["turn_count"],
            "record": filtered_moved_pieces
        }

    # keep the previous record if there are no new moved pieces
    # to faciliate record keeping for granting bishop energize stacks
    # to bishops that perform special captures with their debuff
