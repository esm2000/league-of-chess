import copy
from fastapi import HTTPException, Response
import pytest

import src.api as api
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_white_piece, select_black_piece, 
    move_white_piece, move_black_piece, 
    select_and_move_white_piece, select_and_move_black_piece
)


def test_queen_stun(game):
    # make sure queen stuns when expected to 
    game = clear_game(game)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][4][7] = [{"type": "white_queen"}]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["position_in_play"] = [4, 7]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=7, to_row=4, to_col=3)

    assert game["board_state"][3][3][0]["type"] == "black_pawn"
    assert game["board_state"][3][3][0]["is_stunned"]

    # make sure queen doesn't stun when not expected to
    game = clear_game(game)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][4][7] = [{"type": "white_queen"}]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=7, to_row=4, to_col=6)

    assert game["board_state"][3][3][0]["type"] == "black_pawn"
    assert not game["board_state"][3][3][0].get("is_stunned", False)

    # make sure queen is able to apply stun after it captures a piece,
    # opponent moves, and queen moves but doesn't capture a piece
    game = clear_game(game)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][1][0] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][3][7] = [{"type": "white_queen"}]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["position_in_play"] = [3, 7]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][7] = None
    game_on_next_turn["board_state"][3][3] = [{"type": "white_queen"}]
    game_on_next_turn[ "captured_pieces"] = {"white": ["black_pawn"], "black": []}
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][1][0] = None
    game_on_next_turn["board_state"][2][0] = [{"type": "black_pawn"}]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game_on_next_turn["previous_state"] = copy.deepcopy(game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=3, from_col=3, to_row=3, to_col=0)

    assert game["board_state"][2][0][0]["type"] == "black_pawn"
    assert game["board_state"][2][0][0].get("is_stunned", False) 
    
    # ensure that the player can't move when stunned
    game = clear_game(game)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "white_pawn"}]
    game_on_next_turn["board_state"][4][7] = [{"type": "black_queen"}]
    game_on_next_turn["turn_count"] = 1
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_black_piece(game=game, from_row=4, from_col=7, to_row=4, to_col=4)

    with pytest.raises(Exception):
        # should fail due to the stunned piece being the only piece on white's side, causing a turn skip
        game = select_white_piece(game=game, row=3, col=3)

    with pytest.raises(Exception):
        # should fail due to piece being stunned
        game = move_white_piece(game=game, from_row=3, from_col=3, to_row=2, to_col=3)


def test_stun_cleanse(game):
    # ensure that stuns cleanse after a player moves for their next turn
    game = clear_game(game)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "white_pawn"}]
    game_on_next_turn["board_state"][3][2] = [{"type": "white_pawn"}]
    game_on_next_turn["board_state"][4][7] = [{"type": "black_queen"}]
    game_on_next_turn["turn_count"] = 1
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_black_piece(game=game, from_row=4, from_col=7, to_row=4, to_col=4)

    game = select_and_move_white_piece(game=game, from_row=3, from_col=2, to_row=2, to_col=2)

    game = select_and_move_black_piece(game=game, from_row=4, from_col=4, to_row=4, to_col=5)

    assert game["board_state"][3][3][0]["type"] == "white_pawn"
    assert not game["board_state"][3][3][0].get("is_stunned", False) 


def test_queen_kill_reset(game):
    # test that a queen is able to go again after getting a kill
    # and that queen is automatically in play upon gaining reset
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][1][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][1][7] = [{"type": "black_pawn"}]

    game_on_next_turn["board_state"][3][3] = [{"type": "white_queen"}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    assert game["turn_count"] == 0

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["position_in_play"] = [3, 3]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response(), player=True)
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][1][3] = game_on_next_turn["board_state"][3][3]
    game_on_next_turn["board_state"][3][3] = None
    game_on_next_turn["captured_pieces"]["white"].append(f"black_pawn")

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["position_in_play"] == [1, 3]
    assert game["queen_reset"]
    assert game["queen_reset_type"] == "kill"
    assert game["turn_count"] == 0

    game = move_white_piece(game=game, from_row=1, from_col=3, to_row=4, to_col=0)

    assert not game["queen_reset"]
    assert game["queen_reset_type"] is None
    assert game["turn_count"] == 1


def test_queen_assist_reset(game):
    # test that a queen is able to go again after getting a assist
    # and that queen is automatically in play upon gaining reset
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][1][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][1][7] = [{"type": "black_pawn"}]

    game_on_next_turn["board_state"][3][3] = [{"type": "white_queen"}]
    game_on_next_turn["board_state"][1][2] = [{"type": "white_rook"}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    assert game["turn_count"] == 0

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["position_in_play"] = [1, 2]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][1][3] = game_on_next_turn["board_state"][1][2]
    game_on_next_turn["board_state"][1][2] = None
    game_on_next_turn["captured_pieces"]["white"].append(f"black_pawn")

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["position_in_play"] == [3, 3]
    assert game["queen_reset"]
    assert game["queen_reset_type"] == "assist"
    assert game["turn_count"] == 0

    game = move_white_piece(game=game, from_row=3, from_col=3, to_row=4, to_col=3)

    assert not game["queen_reset"]
    assert game["queen_reset_type"] is None
    assert game["turn_count"] == 1


def test_queen_turn_reset_limitations(game):
    # test that a turn reset with a queen does not enable other non-queen pieces to move and that the turn reset doesn't stack
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][1][3] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][1][7] = [{"type": "black_pawn"}]

    game_on_next_turn["board_state"][3][3] = [{"type": "white_queen"}]
    game_on_next_turn["board_state"][1][2] = [{"type": "white_rook"}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    assert game["turn_count"] == 0

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["position_in_play"] = [1, 2]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][1][3] = game_on_next_turn["board_state"][1][2]
    game_on_next_turn["board_state"][1][2] = None
    game_on_next_turn["captured_pieces"]["white"].append(f"black_pawn")

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["position_in_play"] == [3, 3]
    assert game["queen_reset"]
    assert game["turn_count"] == 0

    with pytest.raises(HTTPException):
        game = select_black_piece(game=game, row=1, col=3)
    
    with pytest.raises(HTTPException):
        game = move_black_piece(game=game, from_row=1, from_col=3, to_row=1, to_col=4)

    game = move_white_piece(game=game, from_row=3, from_col=3, to_row=4, to_col=3)

    assert not game["queen_reset"]
    assert game["turn_count"] == 1

    with pytest.raises(HTTPException):
        game = move_white_piece(game=game, from_row=4, from_col=3, to_row=5, to_col=3)

    game = move_black_piece(game=game, from_row=1, from_col=7, to_row=2, to_col=7)

    assert not game["queen_reset"]
    assert game["turn_count"] == 2



def test_skip_one_turn_if_all_non_king_pieces_are_stunned(game):
    # test that when all non-king pieces are stunned that a turn is skipped (with turn check enabled)
    for side in ["white"]:
        opposite_side = "white" if side == "black" else "black"
        
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][1][0] = [{"type": f"{side}_bishop"}]
        game_on_next_turn["board_state"][2][0] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][6][7] = [{"type": f"{side}_queen"}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_king"}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_pawn"}]
        game_on_next_turn["board_state"][1][1] = [{"type": f"{opposite_side}_pawn"}]

        if side == "black":
            game_on_next_turn["turn_count"] = 1

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        if side == "white":
            assert game["turn_count"] == 0
            game = select_and_move_white_piece(game=game, from_row=6, from_col=7, to_row=1, to_col=2)
            assert game["turn_count"] == 2
        else:
            assert game["turn_count"] == 1
            game = select_and_move_black_piece(game=game, from_row=6, from_col=7, to_row=1, to_col=2)
            assert game["turn_count"] == 3
        
        assert not game["board_state"][0][0][0].get("is_stunned", False)
        assert game["board_state"][0][1][0].get("is_stunned", False)
        assert game["board_state"][1][1][0].get("is_stunned", False)

        assert not game["white_defeat"]
        assert not game["black_defeat"]
        
        
        if side == "white":
            with pytest.raises(HTTPException):
                game = select_black_piece(game=game, row=1, col=1)

            with pytest.raises(HTTPException):
                game = move_black_piece(game=game, from_row=1, from_col=1, to_row=2, to_col=1)

            game = select_and_move_white_piece(game=game, from_row=7, from_col=0, to_row=6, to_col=0)

            assert game["turn_count"] == 3
        else:
            with pytest.raises(HTTPException):
                game = select_white_piece(game=game, row=1, col=1)

            with pytest.raises(HTTPException):
                game = move_white_piece(game=game, from_row=1, from_col=1, to_row=2, to_col=1)

            game = select_and_move_black_piece(game=game, from_row=7, from_col=0, to_row=6, to_col=0)

            assert game["turn_count"] == 4

        assert not game["board_state"][0][0][0].get("is_stunned", False)
        assert not game["board_state"][0][1][0].get("is_stunned", False)
        assert not game["board_state"][1][1][0].get("is_stunned", False)