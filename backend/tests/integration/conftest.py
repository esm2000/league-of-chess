import pytest
from bson.objectid import ObjectId

import src.api as api
from src.database import mongo_client


@pytest.fixture
def game():
    game = api.create_game()
    yield game

    game_database = mongo_client["game_db"]
    game_database["games"].delete_one({"_id": ObjectId(game["id"])})
    game_database["game_moves"].delete_many({"game_id": game["id"]})
    game_database["game_state_history"].delete_many({"game_id": game["id"]})
