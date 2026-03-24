import copy
from fastapi import HTTPException, Response
import pytest

import src.api as api
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_white_piece,
    move_white_piece,
    select_and_move_white_piece
)


def test_bishop_energize_stacks(game):
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)
    
    game_on_next_turn["board_state"][3][3] = [{"type": "white_bishop", "energize_stacks": 0}]
    game_on_next_turn["board_state"][1][1] = [{"type": "black_pawn", "pawn_buff": 0}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_white_piece(game=game, row=3, col=3)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][1][1] = [{"type": "white_bishop", "energize_stacks": 0}]
    game_on_next_turn["board_state"][3][3] = None
    game_on_next_turn["captured_pieces"]["white"].append(f"black_pawn")
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["board_state"][1][1][0]["energize_stacks"] == 20


def test_bishop_debuff_application(game):
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][0][0] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][0][6] = [{"type": "black_pawn", "bishop_debuff": 1}]
    game_on_next_turn["board_state"][6][6] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 3}]
    game_on_next_turn["board_state"][5][1] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_white_piece(game=game, row=5, col=1)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][5][1] = None 
    game_on_next_turn["board_state"][3][3] = [{"type": "white_bishop", "energize_stacks": 0}]
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["board_state"][0][0][0].get("bishop_debuff") == 1
    assert game["board_state"][0][6][0].get("bishop_debuff") == 2
    assert game["board_state"][6][6][0].get("bishop_debuff") == 3
    assert game["board_state"][6][0][0].get("bishop_debuff") == 3


def test_adjacent_capture_of_bishop(game):
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = [{"type": "white_knight"}]
    game_on_next_turn["board_state"][4][5] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][5][5] = [{"type": "black_bishop", "energize_stacks": 0}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_white_piece(game=game, row=3, col=3)

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][3][3] = None 
    game_on_next_turn["board_state"][4][5] = [{"type": "white_knight"}]
    game_on_next_turn["captured_pieces"]["white"].append(f"black_pawn")
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["board_state"][5][5] is None
    assert sorted(game["captured_pieces"]["white"]) == sorted(["black_bishop", "black_pawn"])


def test_full_bishop_debuff_capture(game):
    # test the capturing mechanism for pieces with full bishop debuff stacks
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)

    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    
    original_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_pawn")
    game_on_next_turn["board_state"][6][0] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [6, 0],
        "type": "black_pawn"
    })
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    current_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    energize_stack_difference = current_energize_stack_value - original_energize_stack_value

    assert energize_stack_difference == 10
    assert not game["board_state"][6][0]
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["captured_pieces"]["white"] == ["black_pawn"]
    assert game["bishop_special_captures"] == []


def test_bishop_debuff_double_stack_prevention(game):
    # bishops can be captured by landing on a square diagonally adjacent to it
    # there can be a weird scenario that can lead to double the bishop debuffs 
    # being applied to enemy bishops

    # example situation: 
        # black bishop, posiiton [0, 5]
        # black non-king piece, position [1, 4]
        # black non-king piece, position [1, 6]
        # white bishop, moves to position [2, 5]
        # there can be a bug where the black bishop incorrectly gets two bishop stacks instead of one
    
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][0][5] = [{"type": "black_bishop", "energize_stacks": 0}]
    game_on_next_turn["board_state"][1][4] = [{"type": "black_pawn", "pawn_buff": 0}]
    game_on_next_turn["board_state"][1][6] = [{"type": "black_pawn", "pawn_buff": 0}]
    game_on_next_turn["board_state"][3][4] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=3, from_col=4, to_row=2, to_col=5)

    assert game["board_state"][0][5][0].get("bishop_debuff", 0) == 1
 

def test_full_bishop_debuff_adjacent_application(game):
    # test the capturing mechanism still works when a piece is in danger from being
    # captured adjacently 
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 0}]
    game_on_next_turn["board_state"][7][1] = [{"type": "black_knight", "bishop_debuff": 2}]

    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 95}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)

    assert game["board_state"][6][0][0]["bishop_debuff"] == 1
    
    assert game["board_state"][7][1][0]["bishop_debuff"] == 3

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_knight")
    game_on_next_turn["board_state"][7][1] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [7, 1],
        "type": "black_knight"
    })
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert not game["board_state"][7][1]
    assert game["board_state"][6][0][0]["type"] == "black_pawn"
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["captured_pieces"]["white"] == ["black_knight"]
    assert game["bishop_special_captures"] == []


def test_full_bishop_debuff_spare(game):
    # test the ability for pieces with full bishop debuff stacks to be spared
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)

    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    original_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][6][0][0]["bishop_debuff"] = 0
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())
    
    current_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    energize_stack_difference = current_energize_stack_value - original_energize_stack_value

    assert energize_stack_difference == 0
    assert game["board_state"][6][0][0]["type"] == "black_pawn"
    assert game["board_state"][6][0][0]["bishop_debuff"] == 0
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["bishop_special_captures"] == []


def test_multiple_full_bishop_debuffs(game):
    # ensure that game can handle multiple pieces with full bishop debuff stacks well
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][6][2] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][2][4] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)

    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    assert game["board_state"][6][2][0]["bishop_debuff"] == 3
    assert game["board_state"][2][4][0]["bishop_debuff"] == 3

    original_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_pawn")
    game_on_next_turn["board_state"][6][0] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [6, 0],
        "type": "black_pawn"
    })
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    current_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    energize_stack_difference = current_energize_stack_value - original_energize_stack_value

    assert energize_stack_difference == 10
    assert not game["board_state"][6][0]
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["captured_pieces"]["white"] == ["black_pawn"]
    assert game["bishop_special_captures"] == []

    original_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_pawn")
    game_on_next_turn["board_state"][6][2] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [6, 2],
        "type": "black_pawn"
    })
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())
    
    current_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    energize_stack_difference = current_energize_stack_value - original_energize_stack_value

    assert energize_stack_difference == 10
    assert not game["board_state"][6][2]
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["captured_pieces"]["white"] == ["black_pawn", "black_pawn"]
    assert game["bishop_special_captures"] == []

    original_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][2][4][0]["bishop_debuff"] = 0
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())
    
    current_energize_stack_value = game["board_state"][5][1][0]["energize_stacks"]
    energize_stack_difference = current_energize_stack_value - original_energize_stack_value

    assert energize_stack_difference == 0
    assert game["board_state"][2][4][0]["type"] == "black_pawn"
    assert game["board_state"][2][4][0]["bishop_debuff"] == 0
    assert game["board_state"][5][1][0]["type"] == "white_bishop"
    assert game["bishop_special_captures"] == []


def test_bishop_debuff_capture_increments_turn(game):
    """After capturing the only piece with 3 debuff stacks, turn should increment."""
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    # Bishop move triggers 3rd debuff — turn should NOT increment
    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)
    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    assert game["turn_count"] == 0  # turn extension — still white's turn

    # Capture the debuffed pawn — turn SHOULD increment since no more debuffed pieces
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["captured_pieces"]["white"].append("black_pawn")
    game_on_next_turn["board_state"][6][0] = []
    game_on_next_turn["bishop_special_captures"].append({
        "position": [6, 0],
        "type": "black_pawn"
    })
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["turn_count"] == 1  # should have incremented — all debuffs resolved


def test_bishop_debuff_spare_increments_turn(game):
    """After sparing the only piece with 3 debuff stacks, turn should increment (regression)."""
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)
    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    assert game["turn_count"] == 0

    # Spare the pawn — turn should increment
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][6][0][0]["bishop_debuff"] = 0
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["turn_count"] == 1  # should have incremented — debuff resolved by sparing


def test_full_bishop_debuff_stacks_prevent_other_moves(game):
    # ensure that game prevent other moves from either side when full bishop debuff stacks are present
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][6][0] = [{"type": "black_pawn", "bishop_debuff": 2}]
    game_on_next_turn["board_state"][4][2] = [{"type": "white_bishop", "energize_stacks": 0}]
    
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=4, from_col=2, to_row=5, to_col=1)

    assert game["board_state"][6][0][0]["bishop_debuff"] == 3
    
    with pytest.raises(HTTPException):
        game = move_white_piece(game=game, from_row=6, from_col=0, to_row=5, to_col=0)