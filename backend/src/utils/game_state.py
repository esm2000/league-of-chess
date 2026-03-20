"""Game state lifecycle: initialization, turn counting, persistence, and history management."""

import copy
import datetime

from bson.objectid import ObjectId
from fastapi import HTTPException, Response
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
    expected_version = new_game_state.get("version", 0)
    new_game_state["version"] = expected_version + 1
    query = {"_id": ObjectId(game_id), "version": expected_version}
    game_database = mongo_client["game_db"]
    result = game_database["games"].replace_one(query, new_game_state)
    if result.modified_count == 0:
        raise HTTPException(status_code=409, detail="Game state was modified concurrently")
    save_state_snapshot(new_game_state, mongo_client, game_id)


def save_state_snapshot(game_state: GameState, mongo_client: MongoClient, game_id: str) -> None:
    """Save a snapshot of the current game state to the history collection.

    Called after every successful persist so replay can reconstruct recent turns.
    Automatically prunes snapshots more than 10 turn_count values behind current.
    """
    snapshot = copy.deepcopy(game_state)
    snapshot.pop("previous_state", None)
    snapshot.pop("_id", None)
    snapshot["game_id"] = game_id
    game_database = mongo_client["game_db"]
    game_database["game_state_history"].insert_one(snapshot)

    current_turn = game_state.get("turn_count", 0)
    game_database["game_state_history"].delete_many({
        "game_id": game_id,
        "turn_count": {"$lt": current_turn - 10}
    })


def get_replay_states(game_id: str, mongo_client: MongoClient) -> list[dict]:
    """Return the last 2 completed turns of state snapshots for replay.

    Walks backward through snapshots counting turn_count transitions (where
    turn_count changes between consecutive snapshots). After 2 transitions,
    continues collecting all snapshots at that turn_count boundary, then stops.
    Returns snapshots in ascending version order.
    """
    game_database = mongo_client["game_db"]
    snapshots = list(
        game_database["game_state_history"]
        .find({"game_id": game_id})
        .sort("version", -1)
    )

    if not snapshots:
        return []

    collected = [snapshots[0]]
    transitions = 0
    prev_turn = snapshots[0].get("turn_count")
    boundary_turn = None

    for snap in snapshots[1:]:
        current_turn = snap.get("turn_count")
        if current_turn != prev_turn:
            transitions += 1
            if transitions >= 2 and boundary_turn is None:
                boundary_turn = current_turn
            prev_turn = current_turn

        if boundary_turn is not None and current_turn != boundary_turn:
            break

        collected.append(snap)

    collected.reverse()

    for snap in collected:
        snap.pop("_id", None)

    return collected


def clean_possible_moves_and_possible_captures(new_game_state: GameState) -> None:
    """Clear possible_moves, possible_captures, and unsafe_king_moves from the previous turn."""
    new_game_state["possible_moves"] = []
    new_game_state["possible_captures"] = []
    new_game_state["unsafe_king_moves"] = []


def prevent_client_side_updates_to_graveyard(old_game_state: GameState, new_game_state: GameState) -> None:
    """Overwrite client-submitted graveyard with the server's authoritative copy."""
    new_game_state["graveyard"] = list(old_game_state["graveyard"])


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
