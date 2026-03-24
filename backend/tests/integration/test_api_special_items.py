import copy
from fastapi import Response

import src.api as api
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_and_move_white_piece, select_and_move_black_piece
)


def test_sword_in_the_stone_spawn(game):
    # run a test 25 times and see that the sword in the stone spawns in a suitable location every time
    locations = {}
    for _ in range(5):
        for turn in [9, 19, 29, 39, 49]:
            game = clear_game(game)
            game_on_next_turn = copy.deepcopy(game)
            game_on_next_turn["board_state"][3][3] = [{"type": "black_pawn"}]
            game_on_next_turn["board_state"][3][4] = [{"type": "white_pawn"}]
            game_on_next_turn["turn_count"] = turn

            game_state = api.GameStateRequest(**game_on_next_turn)
            game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
            
            game = select_and_move_black_piece(game=game, from_row=3, from_col=3, to_row=4, to_col=3)

            if tuple(game["sword_in_the_stone_position"]) in locations:
                locations[tuple(game["sword_in_the_stone_position"])] += 1
            else:
                locations[tuple(game["sword_in_the_stone_position"])] = 1

            assert game["turn_count"] == turn + 1
            assert game["sword_in_the_stone_position"] is not None

    for location in locations:
        assert locations[location] < 13
    assert (4, 3) not in locations
    assert (3, 4) not in locations


def test_sword_in_the_stone_retrieval(game):
    # test that both kings can retrieve the sword in the stone and its accompanying buff
    for retrieval_side in ["white", "black"]:
        opposite_side = "white" if retrieval_side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][1][0] = [{"type": "black_pawn"}]
        game_on_next_turn["board_state"][3][3] = [{"type": f"{retrieval_side}_king"}]
        game_on_next_turn["board_state"][3][6] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["turn_count"] = 12 if retrieval_side == "white" else 11
        game_on_next_turn["sword_in_the_stone_position"] = [3, 4]

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        if retrieval_side == "white":
            game = select_and_move_white_piece(game=game, from_row=3, from_col=3, to_row=3, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=3, from_col=3, to_row=3, to_col=4)

        assert game["sword_in_the_stone_position"] is None
        assert game["board_state"][3][4][0]["check_protection"] == 1


def test_sword_in_the_stone_cleared_on_monster_spawn(game):
    # test that the sword in the stone is cleared when a neutral monster spawns on its square
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "white_king"}]
    game_on_next_turn["board_state"][0][4] = [{"type": "black_king"}]
    game_on_next_turn["board_state"][5][0] = [{"type": "white_pawn"}]
    # baron spawns at [3,0] on turn 35
    game_on_next_turn["turn_count"] = 34
    game_on_next_turn["sword_in_the_stone_position"] = [3, 0]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    assert game["sword_in_the_stone_position"] == [3, 0]

    # white moves pawn, turn becomes 35, baron spawns at [3,0] on top of sword
    game = select_and_move_white_piece(game=game, from_row=5, from_col=0, to_row=4, to_col=0)

    assert game["turn_count"] == 35
    assert game["sword_in_the_stone_position"] is None
    assert any(p["type"] == "neutral_baron_nashor" for p in game["board_state"][3][0])


def test_sword_in_the_stone_stacks(game):
    # test that the sword in the stone appropiately stacks
    for retrieval_side in ["white", "black"]:
        opposite_side = "white" if retrieval_side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][1][0] = [{"type": "black_pawn"}]
        game_on_next_turn["board_state"][3][3] = [{"type": f"{retrieval_side}_king", "check_protection": 1}]
        game_on_next_turn["board_state"][3][6] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["turn_count"] = 12 if retrieval_side == "white" else 11
        game_on_next_turn["sword_in_the_stone_position"] = [3, 4]

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        if retrieval_side == "white":
            game = select_and_move_white_piece(game=game, from_row=3, from_col=3, to_row=3, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=3, from_col=3, to_row=3, to_col=4)

        assert game["sword_in_the_stone_position"] is None
        assert game["board_state"][3][4][0]["check_protection"] == 2