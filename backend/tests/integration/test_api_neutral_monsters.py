import copy
from fastapi import HTTPException, Response
import pytest

from mocks.starting_game import starting_game
import src.api as api
from src.utils.game_state import clear_game
from tests.test_utils import (
    select_white_piece, select_black_piece, 
    move_white_piece, move_black_piece, 
    select_and_move_white_piece, select_and_move_black_piece
)


# Helper function to validate dragon buff values on pieces
def validate_dragon_buffs(game, side, expected_buff, piece_positions):
    for row, col in piece_positions:
        pieces = game["board_state"][row][col]
        if pieces:
            for piece in pieces:
                if side in piece.get("type", ""):
                    assert piece.get("dragon_buff", 0) == expected_buff


def test_spawn_monsters(game):
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn['board_state'] = starting_game['board_state']
    game_on_next_turn["turn_count"] = 9
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_black_piece(game=game, from_row=1, from_col=2, to_row=2, to_col=2)

    assert game["board_state"][4][7][0]["type"] == "neutral_dragon"
    assert game["board_state"][3][0][0]["type"] == "neutral_board_herald"

    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["turn_count"] = 34
    game_on_next_turn["sword_in_the_stone_position"] = None
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=6, from_col=2, to_row=5, to_col=2)

    assert game["board_state"][3][0][0]["type"] == "neutral_baron_nashor"
    

def test_neutral_monsters_cannot_move(game):
    conditions_met_for_test = False

    while not conditions_met_for_test:
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)
            
        game_on_next_turn['board_state'][0][0] = [{"type": "black_king"}]
        game_on_next_turn['board_state'][7][7] = [{"type": "white_king"}]
        game_on_next_turn['board_state'][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
        game_on_next_turn['board_state'][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]

        game_on_next_turn["turn_count"] = 9

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        game = select_and_move_black_piece(game=game, from_row=1, from_col=0, to_row=2, to_col=0)

        assert game["turn_count"] == 10
        assert any([piece.get("type") == "neutral_dragon" for piece in game["board_state"][4][7]])
        assert any([piece.get("type") == "neutral_board_herald" for piece in game["board_state"][3][0]])

        # a sword in the stone randomly in the way of the pieces can cause a failure
        if game["sword_in_the_stone_position"] not in [[5, 0]]:
            conditions_met_for_test = True

    with pytest.raises(HTTPException):
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][6] = game_on_next_turn["board_state"][4][7]
        game_on_next_turn["board_state"][4][7] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response())

    with pytest.raises(HTTPException):
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][1] = game_on_next_turn["board_state"][3][0]
        game_on_next_turn["board_state"][3][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response())

    game = select_and_move_white_piece(game=game, from_row=6, from_col=0, to_row=5, to_col=0)

    with pytest.raises(HTTPException):
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][6] = game_on_next_turn["board_state"][4][7]
        game_on_next_turn["board_state"][4][7] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), player=False)

    with pytest.raises(HTTPException):
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][1] = game_on_next_turn["board_state"][3][0]
        game_on_next_turn["board_state"][3][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), player=False)


def test_neutral_monsters_can_be_hurt(game):
    conditions_met_for_test = False

    while not conditions_met_for_test:
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)
            
        game_on_next_turn['board_state'][0][0] = [{"type": "black_king"}]
        game_on_next_turn['board_state'][7][7] = [{"type": "white_king"}]
        game_on_next_turn['board_state'][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
        game_on_next_turn['board_state'][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
        
        game_on_next_turn["board_state"][2][5] = [{"type": "black_bishop"}]
        game_on_next_turn["board_state"][2][7] = [{"type": "black_rook"}]

        game_on_next_turn["board_state"][6][5] = [{"type": "white_bishop"}]
        game_on_next_turn["board_state"][6][7] = [{"type": "white_rook"}]

        game_on_next_turn["turn_count"] = 9

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        game = select_and_move_black_piece(game=game, from_row=1, from_col=0, to_row=2, to_col=0)

        assert game["turn_count"] == 10
        assert any([piece.get("type") == "neutral_dragon" for piece in game["board_state"][4][7]])
        assert any([piece.get("type") == "neutral_board_herald" for piece in game["board_state"][3][0]])
        assert any([piece.get("health", 0) == 5 for piece in game["board_state"][4][7]])
        assert any([piece.get("health", 0) == 5 for piece in game["board_state"][3][0]])

        # a sword in the stone randomly in the way of the pieces can cause a failure
        if game["sword_in_the_stone_position"] not in [[5, 6], [3, 6], [3, 7], [5, 7]]:
            conditions_met_for_test = True

        # landing directly on neutral monster
    game = select_white_piece(game=game, row=6, col=5)
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][6][5][0])
    game_on_next_turn["board_state"][6][5] = None
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response())

    assert game["board_state"][4][7][0]["health"] == 4

    game = select_black_piece(game=game, row=2, col=5)
    
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][2][5][0])
    game_on_next_turn["board_state"][2][5] = None
    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state(game["id"], game_state, Response(), player=False)

    assert game["board_state"][4][7][0]["health"] == 3
    assert any([piece.get("type") == "black_bishop" for piece in game["board_state"][4][7]])
    assert not any([piece.get("type") == "white_bishop" for piece in game["board_state"][4][7]])

    # landing adjacent to neutral monster
    game = select_and_move_white_piece(game=game, from_row=6, from_col=7, to_row=5, to_col=7)

    assert game["board_state"][4][7][0]["health"] == 2
    # Bishops can be captured by landing on any square adjacent to it, even those not on diagonals.
    assert not any([piece.get("type") == "black_bishop" for piece in game["board_state"][4][7]])
    game = select_and_move_black_piece(game=game, from_row=2, from_col=7, to_row=3, to_col=7)
    
    assert game["board_state"][4][7][0]["health"] == 1


def test_neutral_monster_captures_after_spawning_on_any_non_king_piece(game):
    # neutral monster should automatically send non-king pieces to the graveyard
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)

    game_on_next_turn["board_state"][3][7] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][1][1] = [{"type": "black_king"}]
    game_on_next_turn["board_state"][7][1] = [{"type": "white_king"}]
 
    game_on_next_turn["turn_count"] = 9

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
    
    game = select_and_move_black_piece(game=game, from_row=3, from_col=7, to_row=4, to_col=7)

    assert game["turn_count"] == 10
    assert game["board_state"][4][7][0].get("type") == "neutral_dragon"
    assert "black_pawn" in game["graveyard"] 



def test_neutral_monster_ends_game_after_spawning_on_king(game):
    # neutral monster should automatically send non-king pieces to the graveyard
    for side in ["white", "black"]:
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)
        
        game_on_next_turn["board_state"][1][0] = [{"type": "black_pawn"}]

        if side == "black":
            game_on_next_turn["board_state"][3][7] = [{"type": "black_king"}]
            game_on_next_turn["board_state"][7][1] = [{"type": "white_king"}]
        else:
            game_on_next_turn["board_state"][7][1] = [{"type": "black_king"}]
            game_on_next_turn["board_state"][4][7] = [{"type": "white_king"}]
    
        game_on_next_turn["turn_count"] = 9

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        game_on_next_turn = copy.deepcopy(game)
        if side == "black":
            game = select_and_move_black_piece(game=game, from_row=3, from_col=7, to_row=4, to_col=7)
        else:
            game = select_and_move_white_piece(game=game, from_row=7, from_col=1, to_row=7, to_col=2)

        assert (game["board_state"][4][7] or [{}])[0].get("type") == "neutral_dragon"
        if side == "black":
            assert game["black_defeat"]
            assert not game["white_defeat"]
        else:
            assert game["white_defeat"]
            assert not game["black_defeat"]



def test_neutral_monster_health_regen(game):
    # test that neutral monster heals after 6 half-turns (3 full rounds) of not being damaged
    game = clear_game(game)
    game_on_next_turn = copy.deepcopy(game)
    game_on_next_turn["turn_count"] = 11
    game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 5}]

    game_on_next_turn["board_state"][0][0] = [{"type": "black_king"}]
    game_on_next_turn["board_state"][1][1] = [{"type": "black_pawn"}]
    game_on_next_turn["board_state"][7][7] = [{"type": "white_king"}]
    game_on_next_turn["board_state"][2][7] = [{"type": "black_pawn"}]

    game_state = api.GameStateRequest(**game_on_next_turn)
    game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

    # Black pawn moves adjacent to dragon — deals damage (turn 11→12)
    game = select_and_move_black_piece(game=game, from_row=2, from_col=7, to_row=3, to_col=7)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 12

    # 5 idle moves — monster should NOT heal yet (only 5 half-turns since damage)
    game = select_and_move_white_piece(game=game, from_row=7, from_col=7, to_row=7, to_col=6)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 13

    game = select_and_move_black_piece(game=game, from_row=0, from_col=0, to_row=0, to_col=1)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 14

    game = select_and_move_white_piece(game=game, from_row=7, from_col=6, to_row=7, to_col=5)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 15

    game = select_and_move_black_piece(game=game, from_row=0, from_col=1, to_row=0, to_col=0)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 16

    game = select_and_move_white_piece(game=game, from_row=7, from_col=5, to_row=7, to_col=6)
    assert game["board_state"][4][7][0]["health"] == 4
    assert game["turn_count"] == 17

    # 6th idle half-turn — monster heals to full (6 half-turns = 3 full rounds)
    game = select_and_move_black_piece(game=game, from_row=0, from_col=0, to_row=0, to_col=1)
    assert game["board_state"][4][7][0]["health"] == 5
    assert game["turn_count"] == 18


def test_check_by_neutral_monster(game):
    # test that the game ends when a king stays near a neutral monster
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"

        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][5][7] = [{"type": f"{side}_king"}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][0] = [{"type": f"black_rook"}]
        game_on_next_turn["turn_count"] = 9

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["position_in_play"] = [0, 0]
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), player=False)

        game_on_next_turn = copy.deepcopy(game)
        
        game_on_next_turn["board_state"][0][1] = game_on_next_turn["board_state"][0][0]
        game_on_next_turn["board_state"][0][0] = None

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), player=False)
        
        assert not game[f"{side}_defeat"] and not game[f"{opposite_side}_defeat"]
        assert all(["king" in piece.get("type") for piece in game["board_state"][5][7]])
        assert any([piece.get("type") == "neutral_dragon" for piece in game["board_state"][4][7]])
        assert game["check"][side] and not game["check"][opposite_side]            

        if side == "white":
            game = select_white_piece(game=game, row=5, col=7)
        else:
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
            game = select_black_piece(game=game, row=5, col=7)

        # must get out of check
        with pytest.raises(HTTPException):
            if side == "white":
                game = move_white_piece(game=game, from_row=5, from_col=7, to_row=5, to_col=6)
            else:
                game = move_black_piece(game=game, from_row=5, from_col=7, to_row=5, to_col=6)

        if side == "white":
            game = move_white_piece(game=game, from_row=5, from_col=7, to_row=6, to_col=7)
        else:
            game = move_black_piece(game=game, from_row=5, from_col=7, to_row=6, to_col=7)

        assert not game[f"{side}_defeat"] and not game[f"{opposite_side}_defeat"]
        assert all(["king" in piece.get("type") for piece in game["board_state"][6][7]])
        assert not game["check"][side] and not game["check"][opposite_side]



def test_capture_behavior_when_neutral_and_normal_piece_are_on_same_square(game):
    # test both when the neutral monster has over 1hp and when it has 1 hp
    for test_case in ["damage", "slay"]:
        conditions_met_for_test = False

        while not conditions_met_for_test:
            game = clear_game(game)
            game_on_next_turn = copy.deepcopy(game)

            game_on_next_turn["board_state"][0][0] = [{"type": f"white_king"}]
            game_on_next_turn["board_state"][7][0] = [{"type": f"black_king"}]
            game_on_next_turn["board_state"][1][7] = [{"type": f"white_rook"}]
            game_on_next_turn["board_state"][7][7] = [{"type": f"black_rook"}]

            game_on_next_turn["turn_count"] = 9

            game_state = api.GameStateRequest(**game_on_next_turn)
            game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

            game = select_and_move_black_piece(game=game, from_row=7, from_col=0, to_row=6, to_col=0)

            # a sword in the stone randomly in the way of the pieces can cause a failure
            if game["sword_in_the_stone_position"] not in [[2, 7], [3, 7], [5, 7], [6, 7]]:
                conditions_met_for_test = True
        
        if test_case == "slay":
            game_on_next_turn = copy.deepcopy(game)
            game_on_next_turn["board_state"][4][7][0]["health"] = 2
            game_state = api.GameStateRequest(**game_on_next_turn)
            game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        game = select_white_piece(game=game, row=1, col=7)

        game_on_next_turn = copy.deepcopy(game)
        white_rook = game_on_next_turn["board_state"][1][7][0]
        game_on_next_turn["board_state"][4][7].append(white_rook)
        game_on_next_turn["board_state"][1][7] = None

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response())
        
        assert len(game["board_state"][4][7]) == 2
        assert game["board_state"][4][7][0].get("health", -1) == (4 if test_case == "damage" else 1)

        game = select_black_piece(game=game, row=7, col=7)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["captured_pieces"]["black"].append("white_rook")
        game_on_next_turn["gold_count"]["black"] = 10
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][7][0])
        game_on_next_turn["board_state"][4][7].remove(white_rook)
        game_on_next_turn["board_state"][7][7] = None

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), player=False)

        if test_case == "damage":
            assert len(game["board_state"][4][7]) == 2
            assert game["board_state"][4][7][0].get("health", -1) == 3
            assert game["board_state"][4][7][1]["type"] == "black_rook"
        else:
            assert len(game["board_state"][4][7]) == 1
            assert game["board_state"][4][7][0]["type"] == "black_rook"
            assert "neutral_dragon" in game["captured_pieces"]["black"]


def test_buff_acquired_from_dragon_slain_stack_1(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight"}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop"}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king"}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen"}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["turn_count"] = 2 if side == "white" else 1

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 1
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 3 if side == "white" else 2
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]
        
        # only the pawns should gain the dragon buff
        validate_dragon_buffs(game, side, 1, [(6, 0), (6, 1)])
        validate_dragon_buffs(game, side, 0, [(7, 0), (7, 1), (7, 2), (7, 3), (4, 7)])

        # enemy pieces should never gain the dragon buff
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])
        
        if side == "white":
            game = select_and_move_black_piece(game=game, from_row=0, from_col=0, to_row=1, to_col=0)
        else:
            game = select_and_move_white_piece(game=game, from_row=0, from_col=0, to_row=1, to_col=0)

        # buffs should remain after enemy turn
        validate_dragon_buffs(game, side, 1, [(6, 0), (6, 1)])
        validate_dragon_buffs(game, side, 0, [(7, 0), (7, 1), (7, 2), (7, 3), (4, 7)])

        validate_dragon_buffs(game, opposite_side, 0, [(1, 0), (0, 1)])

        
def test_buff_acquired_from_dragon_slain_stack_2(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight"}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop"}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king"}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen"}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 1
        game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

        game_on_next_turn["turn_count"] = 42 if side == "white" else 41

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 2
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # all allied pieces should gain the dragon buff
        validate_dragon_buffs(game, side, 2, [(6, 0), (6, 1), (7, 0), (7, 1), (7, 2), (7, 3), (4, 7)])

        # enemy pieces should never gain the dragon buff
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])
        
        if side == "white":
            game = select_and_move_black_piece(game=game, from_row=0, from_col=0, to_row=1, to_col=0)
        else:
            game = select_and_move_white_piece(game=game, from_row=0, from_col=0, to_row=1, to_col=0)

        # buffs should remain after enemy turn
        validate_dragon_buffs(game, side, 2, [(6, 0), (6, 1), (7, 0), (7, 1), (7, 2), (7, 3), (4, 7)])

        validate_dragon_buffs(game, opposite_side, 0, [(1, 0), (0, 1)])


def test_buff_acquired_from_dragon_slain_stack_3(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 2}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 2}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook", "dragon_buff": 2}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight", "dragon_buff": 2}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop", "dragon_buff": 2}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king", "dragon_buff": 2}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen", "dragon_buff": 2}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 2
        game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

        game_on_next_turn["turn_count"] = 42 if side == "white" else 41

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 3
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # validate that all pieces have dragon buff of 3
        validate_dragon_buffs(game, side, 3, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

        # validate that enemy pieces don't have any dragon buffs
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])


def test_buff_acquired_from_dragon_slain_stack_4(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook", "dragon_buff": 3}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight", "dragon_buff": 3}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop", "dragon_buff": 3}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king", "dragon_buff": 3}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen", "dragon_buff": 3}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 3
        game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

        game_on_next_turn["turn_count"] = 42 if side == "white" else 41

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 4
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # validate that all pieces have dragon buff of 4
        validate_dragon_buffs(game, side, 4, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

        # validate that enemy pieces don't have any dragon buffs
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])


def test_buff_acquired_from_dragon_slain_stack_5(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen", "dragon_buff": 4}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 4
        game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

        game_on_next_turn["turn_count"] = 42 if side == "white" else 41

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 5
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

        # validate that enemy pieces don't have any dragon buffs
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])


def test_buff_acquired_from_dragon_slain_stack_5_duration(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_rook", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king", "dragon_buff": 4}]
        game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_queen", "dragon_buff": 4}]

        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]

        game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 4
        game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

        game_on_next_turn["turn_count"] = 42 if side == "white" else 41

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
        
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # turn 0
        if side == "white":
            game = select_white_piece(game=game, row=7, col=4)
        else:
            game = select_black_piece(game=game, row=7, col=4)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
        game_on_next_turn["board_state"][7][4] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 5
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

        # validate that enemy pieces don't have any dragon buffs
        validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])
        
        if opposite_side == "black":
            game = select_and_move_black_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)
        else:
            game = select_and_move_white_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)

        # turn 1
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 4), (7, 2)])

        if opposite_side == "black":
            game = select_and_move_black_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
        else:
            game = select_and_move_white_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)

        # turn 2
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

        if opposite_side == "black":
            game = select_and_move_black_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)
        else:
            game = select_and_move_white_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)

        # turn 3
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 4), (7, 2)])

        if opposite_side == "black":
            game = select_and_move_black_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
        else:
            game = select_and_move_white_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
        
        # turn 4
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        # validate that all pieces have dragon buff of 4
        validate_dragon_buffs(game, side, 4, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])


def test_buff_acquired_from_dragon_slain_restack_5_after_expiration(game):
    for side in ["white", "black"]:
        conditions_met_for_test = False
        while not conditions_met_for_test:
            opposite_side = "white" if side == "black" else "black"
            game = clear_game(game)
            game_on_next_turn = copy.deepcopy(game)

            game_on_next_turn["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1}]

            game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
            game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
            game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_rook", "dragon_buff": 4}]
            game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_knight", "dragon_buff": 4}]
            game_on_next_turn["board_state"][7][4] = [{"type": f"{side}_bishop", "dragon_buff": 4}]
            game_on_next_turn["board_state"][7][2] = [{"type": f"{side}_king", "dragon_buff": 4}]
            game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_queen", "dragon_buff": 4}]

            game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]
            game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_king"}]
            game_on_next_turn["board_state"][0][7] = [{"type": f"{opposite_side}_rook"}]

            game_on_next_turn["neutral_buff_log"][side]["dragon"]["stacks"] = 4
            game_on_next_turn["neutral_buff_log"][side]["dragon"]["turn"] = 32

            game_on_next_turn["turn_count"] = 42 if side == "white" else 41

            game_state = api.GameStateRequest(**game_on_next_turn)
            game = api.update_game_state_no_restrictions(game["id"], game_state, Response())
            
            assert not game["neutral_buff_log"][side]["board_herald"]["active"]
            assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

            assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
            assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
            assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
            assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

            # turn 0
            if side == "white":
                game = select_white_piece(game=game, row=7, col=4)
            else:
                game = select_black_piece(game=game, row=7, col=4)

            game_on_next_turn = copy.deepcopy(game)
            game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][4][0])
            game_on_next_turn["board_state"][7][4] = None
            game_state = api.GameStateRequest(**game_on_next_turn)
            game = api.update_game_state(game["id"], game_state, Response(), side == "white")

            assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_bishop"

            assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 5
            assert game["neutral_buff_log"][side]["dragon"]["turn"] == 43 if side == "white" else 42
            assert not game["neutral_buff_log"][side]["board_herald"]["active"]
            assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

            assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
            assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
            assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
            assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

            # validate that all pieces have dragon buff of 5
            validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

            # validate that enemy pieces don't have any dragon buffs
            validate_dragon_buffs(game, opposite_side, 0, [(0, 0), (0, 1)])
            
            if opposite_side == "black":
                game = select_and_move_black_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)
            else:
                game = select_and_move_white_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)

            # turn 1
            if side == "white":
                game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
            else:
                game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

            # validate that all pieces have dragon buff of 5
            validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 4), (7, 2)])

            if opposite_side == "black":
                game = select_and_move_black_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
            else:
                game = select_and_move_white_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)

            # turn 2
            if side == "white":
                game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
            else:
                game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

            # validate that all pieces have dragon buff of 5
            validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])

            if opposite_side == "black":
                game = select_and_move_black_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)
            else:
                game = select_and_move_white_piece(game=game, from_row=0, from_col=1, to_row=1, to_col=1)

            # turn 3
            if side == "white":
                game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
            else:
                game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

            # validate that all pieces have dragon buff of 5
            validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 4), (7, 2)])

            if opposite_side == "black":
                game = select_and_move_black_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
            else:
                game = select_and_move_white_piece(game=game, from_row=1, from_col=1, to_row=0, to_col=1)
            
            # turn 4 (expiration)
            if side == "white":
                game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
            else:
                game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

            # validate that all pieces have dragon buff of 4
            validate_dragon_buffs(game, side, 4, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 3), (7, 2)])
            
            # a sword in the stone randomly in the way of the pieces can cause a failure
            # second phase moves pieces along col 7: rook [7,3]->[7,7], enemy rook [0,7]->[3,7]
            if game["sword_in_the_stone_position"] not in [[7, 4], [7, 5], [7, 6], [7, 7], [6, 7], [5, 7], [3, 7], [2, 7], [1, 7]]:
                conditions_met_for_test = True

        # position pieces to slay dragon again
        if opposite_side == "white":
            game = select_and_move_white_piece(game, from_row=0, from_col=1, to_row=0, to_col=2)
        else:
            game = select_and_move_black_piece(game, from_row=0, from_col=1, to_row=0, to_col=2)
        
        if side == "white":
            game = select_and_move_white_piece(game, from_row=7, from_col=3, to_row=7, to_col=7)
        else:
            game = select_and_move_black_piece(game, from_row=7, from_col=3, to_row=7, to_col=7)

        if opposite_side == "white":
            game = select_and_move_white_piece(game, from_row=0, from_col=2, to_row=0, to_col=1)
        else:
            game = select_and_move_black_piece(game, from_row=0, from_col=2, to_row=0, to_col=1)

        # damage dragon from 5 hp to 3 hp
        if side == "white":
            game = select_white_piece(game=game, row=7, col=7)
        else:
            game = select_black_piece(game=game, row=7, col=7)
        
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][7][0])
        game_on_next_turn["board_state"][7][7] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")
        
        assert game["board_state"][4][7][0].get("health", 0) == 3

        # damage dragon from 3 hp to 2 hp
        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=3, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=3, to_col=7)

        # move white rook away from dragon to avoid getting slain
        if side == "white":
            game = select_white_piece(game=game, row=4, col=7)
        else:
            game = select_black_piece(game=game, row=4, col=7)

        piece_index = -1
        square = game["board_state"][4][7] or []
        for i in range(len(square)):
            piece = square[i]
            if side in piece.get("type"):
                piece_index = i
        
        game_on_next_turn = copy.deepcopy(game)
        piece = game_on_next_turn["board_state"][4][7].pop(piece_index)
        game_on_next_turn["board_state"][7][7] = [piece]
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")
        
        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=3, from_col=7, to_row=0, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=3, from_col=7, to_row=0, to_col=7)
        
        # deal final blow to dragon
        if side == "white":
            game = select_white_piece(game=game, row=7, col=7)
        else:
            game = select_black_piece(game=game, row=7, col=7)
        
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][4][7].append(game_on_next_turn["board_state"][7][7][0])
        game_on_next_turn["board_state"][7][7] = None
        game_state = api.GameStateRequest(**game_on_next_turn)

        game = api.update_game_state(game["id"], game_state, Response(), side == "white")
        
        assert len(game["board_state"][4][7]) == 1 and game["board_state"][4][7][0].get("type") == f"{side}_rook"
        
        # validate that all pieces have dragon buff of 5
        validate_dragon_buffs(game, side, 5, [(6, 0), (6, 1), (7, 0), (7, 1), (4, 7), (7, 2)])
            

def test_buff_acquired_from_board_herald_slain(game):
    # validate neutral_monster_log update + buffs granted
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][3][0] = [{"type": "neutral_board_herald", "health": 1}]
        
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_king"}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][1][0] = [{"type": f"{side}_rook"}]

        game_on_next_turn["board_state"][0][7] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_rook"}]


        game_on_next_turn["turn_count"] = 22 if side == "white" else 21

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=1, col=0)
        else:
            game = select_black_piece(game=game, row=1, col=0)
        
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][0].append(game_on_next_turn["board_state"][1][0][0])
        game_on_next_turn["board_state"][1][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")
        
        assert len(game["board_state"][3][0]) == 1 and game["board_state"][3][0][0].get("type") == f"{side}_rook"

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # only the capturing piece should gain the board herald buff
        assert game["board_state"][3][0][0].get("board_herald_buff", False)
        assert not game["board_state"][7][0][0].get("board_herald_buff", False)
        assert not game["board_state"][7][1][0].get("board_herald_buff", False)
        assert not game["board_state"][6][0][0].get("board_herald_buff", False)
        assert not game["board_state"][6][1][0].get("board_herald_buff", False)

        assert not game["board_state"][0][7][0].get("board_herald_buff", False)
        assert not game["board_state"][0][1][0].get("board_herald_buff", False)

        # buffs should remain after enemy turn
        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        assert game["board_state"][3][0][0].get("board_herald_buff", False)
        assert not game["board_state"][7][0][0].get("board_herald_buff", False)
        assert not game["board_state"][7][1][0].get("board_herald_buff", False)
        assert not game["board_state"][6][0][0].get("board_herald_buff", False)
        assert not game["board_state"][6][1][0].get("board_herald_buff", False)

        assert not game["board_state"][0][6][0].get("board_herald_buff", False)
        assert not game["board_state"][0][1][0].get("board_herald_buff", False)


def test_buff_acquired_from_board_herald_slain_duration(game):
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][3][0] = [{"type": "neutral_board_herald", "health": 1}]

        game_on_next_turn["board_state"][1][0] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king"}]

        game_on_next_turn["board_state"][0][7] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]

        game_on_next_turn["turn_count"] = 22 if side == "white" else 21

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        # turn 0: kill board herald
        if side == "white":
            game = select_white_piece(game=game, row=1, col=0)
        else:
            game = select_black_piece(game=game, row=1, col=0)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][0].append(game_on_next_turn["board_state"][1][0][0])
        game_on_next_turn["board_state"][1][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["board_state"][3][0][0].get("board_herald_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 1
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["board_state"][3][0][0].get("board_herald_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)

        # turn 2
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["board_state"][3][0][0].get("board_herald_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 3
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["board_state"][3][0][0].get("board_herald_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)

        # turn 4 (last active turn)
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        assert game["neutral_buff_log"][side]["board_herald"]["active"]
        assert game["board_state"][3][0][0].get("board_herald_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 5 (buff should have expired)
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["board_state"][3][0][0].get("board_herald_buff", False)


def test_buff_acquired_from_baron_nashor_slain(game):
    # validate neutral_monster_log update + buffs granted
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][3][0] = [{"type": "neutral_baron_nashor", "health": 1}]
        
        game_on_next_turn["board_state"][7][0] = [{"type": f"{side}_king"}]
        game_on_next_turn["board_state"][7][1] = [{"type": f"{side}_rook"}]
        
        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][1][0] = [{"type": f"{side}_rook"}]

        game_on_next_turn["board_state"][0][7] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][1] = [{"type": f"{opposite_side}_rook"}]
        game_on_next_turn["board_state"][1][6] = [{"type": f"{opposite_side}_pawn"}]


        game_on_next_turn["turn_count"] = 52 if side == "white" else 51

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        if side == "white":
            game = select_white_piece(game=game, row=1, col=0)
        else:
            game = select_black_piece(game=game, row=1, col=0)
        
        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][0].append(game_on_next_turn["board_state"][1][0][0])
        game_on_next_turn["board_state"][1][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")
        
        assert len(game["board_state"][3][0]) == 1 and game["board_state"][3][0][0].get("type") == f"{side}_rook"

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["neutral_buff_log"][side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][side]["board_herald"]["active"]

        assert game["neutral_buff_log"][opposite_side]["dragon"]["stacks"] == 0
        assert game["neutral_buff_log"][opposite_side]["dragon"]["turn"] == 0
        assert not game["neutral_buff_log"][opposite_side]["board_herald"]["active"]
        assert not game["neutral_buff_log"][opposite_side]["baron_nashor"]["active"]

        # only allied pawns should receive buff
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)
        assert not game["board_state"][3][0][0].get("baron_nashor_buff", False)
        assert not game["board_state"][7][0][0].get("baron_nashor_buff", False)
        assert not game["board_state"][7][1][0].get("baron_nashor_buff", False)

        assert not game["board_state"][0][7][0].get("baron_nashor_buff", False)
        assert not game["board_state"][0][1][0].get("baron_nashor_buff", False)
        assert not game["board_state"][1][6][0].get("baron_nashor_buff", False)

        # buffs should remain after enemy turn
        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)
        assert not game["board_state"][3][0][0].get("baron_nashor_buff", False)
        assert not game["board_state"][7][0][0].get("baron_nashor_buff", False)
        assert not game["board_state"][7][1][0].get("baron_nashor_buff", False)

        assert not game["board_state"][0][6][0].get("baron_nashor_buff", False)
        assert not game["board_state"][0][1][0].get("baron_nashor_buff", False)
        assert not game["board_state"][1][6][0].get("baron_nashor_buff", False)


def test_buff_acquired_from_baron_nashor_slain_duration(game):
    # Before rook kills baron:                           After rook kills baron:
    ##    0  1  2  3  4  5  6  7                         ##    0  1  2  3  4  5  6  7
    ## 0 |br|##|__|##|__|##|__|bK|                       ## 0 |br|##|__|##|__|##|__|bK|
    ## 1 |wr|__|##|__|##|__|##|__|                       ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|                       ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |BN|__|##|__|##|__|##|__|                       ## 3 |wr|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|                       ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|                       ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |wp|wp|__|##|__|##|__|##|                       ## 6 |wp|wp|__|##|__|##|__|##|
    ## 7 |##|__|##|wK|##|__|##|__|                       ## 7 |##|__|##|wK|##|__|##|__|
    #
    ##    0  1  2  3  4  5  6  7                         ##    0  1  2  3  4  5  6  7
    ## 0 |wr|##|__|##|__|##|__|wK|                       ## 0 |wr|##|__|##|__|##|__|wK|
    ## 1 |br|__|##|__|##|__|##|__|                       ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|                       ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |BN|__|##|__|##|__|##|__|                       ## 3 |br|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|                       ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|                       ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |bp|bp|__|##|__|##|__|##|                       ## 6 |bp|bp|__|##|__|##|__|##|
    ## 7 |##|__|##|bK|##|__|##|__|                       ## 7 |##|__|##|bK|##|__|##|__|
    #
    # After baron kill, king shuffles [7][3] <-> [7][4] while
    # opposite king shuffles [0][7] <-> [0][6] to advance turns.
    # Baron buff should last 4 game turns (turns 1-4) then expire on turn 5.
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        game = clear_game(game)
        game_on_next_turn = copy.deepcopy(game)

        game_on_next_turn["board_state"][3][0] = [{"type": "neutral_baron_nashor", "health": 1}]

        game_on_next_turn["board_state"][1][0] = [{"type": f"{side}_rook"}]
        game_on_next_turn["board_state"][6][0] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][6][1] = [{"type": f"{side}_pawn"}]
        game_on_next_turn["board_state"][7][3] = [{"type": f"{side}_king"}]

        game_on_next_turn["board_state"][0][7] = [{"type": f"{opposite_side}_king"}]
        game_on_next_turn["board_state"][0][0] = [{"type": f"{opposite_side}_rook"}]

        game_on_next_turn["turn_count"] = 52 if side == "white" else 51

        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state_no_restrictions(game["id"], game_state, Response())

        # turn 0: kill baron
        if side == "white":
            game = select_white_piece(game=game, row=1, col=0)
        else:
            game = select_black_piece(game=game, row=1, col=0)

        game_on_next_turn = copy.deepcopy(game)
        game_on_next_turn["board_state"][3][0].append(game_on_next_turn["board_state"][1][0][0])
        game_on_next_turn["board_state"][1][0] = None
        game_state = api.GameStateRequest(**game_on_next_turn)
        game = api.update_game_state(game["id"], game_state, Response(), side == "white")

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 1
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)

        # turn 2
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 3
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=6, to_row=0, to_col=7)

        # turn 4 (last active turn)
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=4, to_row=7, to_col=3)

        assert game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert game["board_state"][6][1][0].get("baron_nashor_buff", False)

        if opposite_side == "white":
            game = select_and_move_white_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)
        else:
            game = select_and_move_black_piece(game=game, from_row=0, from_col=7, to_row=0, to_col=6)

        # turn 5 (buff should have expired)
        if side == "white":
            game = select_and_move_white_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)
        else:
            game = select_and_move_black_piece(game=game, from_row=7, from_col=3, to_row=7, to_col=4)

        assert not game["neutral_buff_log"][side]["baron_nashor"]["active"]
        assert not game["board_state"][6][0][0].get("baron_nashor_buff", False)
        assert not game["board_state"][6][1][0].get("baron_nashor_buff", False)
