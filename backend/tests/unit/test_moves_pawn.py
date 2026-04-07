import copy
import src.moves as moves
from mocks.empty_game import empty_game


def test_pawn_movement():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3][3] = [{"type": f"{side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)

        curr_position = [3, 3]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)
        assert [[2 if side == 'white' else 4, 3]] == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0



def test_pawn_capture():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|bp|##|bK|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|wp|__|wK|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3 if side == 'white' else 4][2] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][3 if side == 'white' else 4][4] = [{"type": f"{side}_king"}]
        curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{"type": f"{opposite_side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][4 if side == 'white' else 3][2] = copy.deepcopy(curr_game_state["board_state"][3 if side == 'white' else 4][2])
        prev_game_state["board_state"][3 if side == 'white' else 4][2] = None

        curr_position = [2 if side == 'white' else 5, 3]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[3 if side == 'white' else 4, 3], [3 if side == 'white' else 4, 2]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert [[[3 if side == 'white' else 4, 2], [3 if side == 'white' else 4, 2]]] == possible_moves_and_captures["possible_captures"]
        

def test_blocked_pawn():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|bK|bp|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|wK|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3 if side == 'white' else 4][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][3 if side == 'white' else 4][2] = [{"type": f"{side}_king"}]
        curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{"type": f"{opposite_side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][4 if side == 'white' else 3][2] = copy.deepcopy(curr_game_state["board_state"][3 if side == 'white' else 4][2])
        prev_game_state["board_state"][3 if side == 'white' else 4][2] = None

        curr_position = [2 if side == 'white' else 5, 3]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert len(possible_moves_and_captures["possible_moves"]) == 0
        assert len(possible_moves_and_captures["possible_captures"]) == 0


def test_buffed_pawn_capture():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        for pawn_buff in [1, 2]:
            curr_game_state = copy.deepcopy(empty_game)
            curr_game_state["board_state"][3 if side == 'white' else 4][3] = [{"type": f"{side}_pawn"}]
            curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{
                                                                    "type": f"{opposite_side}_pawn",
                                                                    "pawn_buff": pawn_buff
                                                                }]

            prev_game_state = copy.deepcopy(curr_game_state)
            prev_game_state["board_state"][4 if side == 'white' else 3][3] = copy.deepcopy(curr_game_state["board_state"][3 if side == 'white' else 4][3])
            prev_game_state["board_state"][3 if side == 'white' else 4][3] = None

            curr_position = [2 if side == 'white' else 5, 3]

            possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

            assert sorted([[3 if side == 'white' else 4, 3]]) == sorted(possible_moves_and_captures["possible_moves"])
            assert [[[3 if side == 'white' else 4, 3], [3 if side == 'white' else 4, 3]]] == possible_moves_and_captures["possible_captures"]


def test_buffed_pawn_invicibility():
     ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|bp|##|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|wp|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3 if side == 'white' else 4][2] = [{
                                                                "type": f"{side}_pawn",
                                                                "pawn_buff": 2
                                                            }]
        curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{
                                                                "type": f"{opposite_side}_pawn"
                                                            }]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][4 if side == 'white' else 3][2] = copy.deepcopy(curr_game_state["board_state"][3 if side == 'white' else 4][2])
        prev_game_state["board_state"][3 if side == 'white' else 4][2] = None

        curr_position = [2 if side == 'white' else 5, 3]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[3 if side == 'white' else 4, 3]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0


def test_pawn_interactions_with_neutral_monster():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|nd|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|nd|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3 if side == 'white' else 4][3] = [{
                                                                "type": "neutral_dragon",
                                                            }]
        curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{
                                                                "type": f"{opposite_side}_pawn"
                                                            }]

        prev_game_state = copy.deepcopy(curr_game_state)

        curr_position = [2 if side == 'white' else 5, 3]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[3 if side == 'white' else 4, 3]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|nd|##|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|nd|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for health in [5, 1]:
        for side in ["white", "black"]:
            opposite_side = "black" if side == "white" else "white"
            for boss in ["dragon", "baron_nashor", "board_herald"]:
                curr_game_state = copy.deepcopy(empty_game)
                curr_game_state["board_state"][3 if side == 'white' else 4][2] = [{
                                                                        "type": f"neutral_{boss}",
                                                                        "health": health
                                                                    }]
                curr_game_state["board_state"][2 if side == 'white' else 5][3] = [{
                                                                        "type": f"{opposite_side}_pawn"
                                                                    }]

                prev_game_state = copy.deepcopy(curr_game_state)

                curr_position = [2 if side == 'white' else 5, 3]

                possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

                assert sorted([[3 if side == 'white' else 4, 3], [3 if side == 'white' else 4, 2]]) == sorted(possible_moves_and_captures["possible_moves"])
                if health != 1:
                    assert len(possible_moves_and_captures["possible_captures"]) == 0
                else:
                    assert [[[3 if side == 'white' else 4, 2], [3 if side == 'white' else 4, 2]]] == possible_moves_and_captures["possible_captures"]


def test_pawn_starting_position():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|wp|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|bp|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][1 if side == 'black' else 6][2] = [{"type": f"{'black' if side == 'black' else 'white'}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        
        curr_position = [1 if side == 'black' else 6, 2]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[2 if side == 'black' else 5, 2], [3 if side == 'black' else 4, 2]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|bk|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|wp|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|bp|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|wk|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][1 if side == 'black' else 6][2] = [{"type": f"{'black' if side == 'black' else 'white'}_pawn"}]
        curr_game_state["board_state"][3 if side == 'black' else 4][2] = [{"type": f"{'white' if side == 'black' else 'black'}_knight"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][4 if side == 'black' else 3][4] = copy.deepcopy(curr_game_state["board_state"][3 if side == 'black' else 4][2])
        prev_game_state["board_state"][3 if side == 'black' else 4][2] = None
        
        curr_position = [1 if side == 'black' else 6, 2]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[2 if side == 'black' else 5, 2]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0


    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|bq|__|##|__|##|__|
    ## 6 |__|##|wp|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|bp|__|##|__|##|__|
    ## 2 |__|##|wq|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][1 if side == 'black' else 6][2] = [{"type": f"{'black' if side == 'black' else 'white'}_pawn"}]
        curr_game_state["board_state"][2 if side == 'black' else 5][2] = [{"type": f"{'white' if side == 'black' else 'black'}_queen"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][7 if side == 'black' else 0][2] = copy.deepcopy(curr_game_state["board_state"][2 if side == 'black' else 5][2])
        prev_game_state["board_state"][2 if side == 'black' else 5][2] = None
        
        curr_position = [1 if side == 'black' else 6, 2]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert len(possible_moves_and_captures["possible_captures"]) == 0
        assert len(possible_moves_and_captures["possible_captures"]) == 0



def test_pawn_second_move():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|wp|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|bp|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][5 if side == 'white' else 2][2] = [{"type": f"{side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)

        curr_position = [5 if side == 'white' else 2, 2]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[4 if side == 'white' else 3, 2]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert len(possible_moves_and_captures["possible_captures"]) == 0


def test_pawn_en_passant_capture():

    ##    0  1  2  3  4  5  6  7                ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|              ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|bp|##|__|##|__|              ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|              ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|wp|__|##|__|              ## 3 |##|__|##|bp|wp|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|              ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|              ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|              ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|              ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7                ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|              ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|              ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|              ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|              ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|bp|##|__|##|              ## 4 |__|##|__|wp|bp|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|              ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|wp|__|##|__|##|              ## 6 |__|##|__|##|__|##|__|##| 
    ## 7 |##|__|##|__|##|__|##|__|              ## 7 |##|__|##|__|##|__|##|__|
    
    for side in ["white", "black"]:
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][4 if side == 'black' else 3][4] = [{"type": f"{'black' if side == 'black' else 'white'}_pawn"}]
        curr_game_state["board_state"][4 if side == 'black' else 3][3] = [{"type": f"{'white' if side == 'black' else 'black'}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][6 if side == 'black' else 1][3] = [{"type": f"{'white' if side == 'black' else 'black'}_pawn"}]
        prev_game_state["board_state"][4 if side == 'black' else 3][3] = None

        curr_position = [4 if side == 'black' else 3, 4]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

        assert sorted([[5 if side == 'black' else 2, 4], [5 if side == 'black' else 2, 3]]) == sorted(possible_moves_and_captures["possible_moves"])
        assert [[[5 if side == 'black' else 2, 3], [4 if side == 'black' else 3, 3]]] == possible_moves_and_captures["possible_captures"]


def test_pawn_en_passant_negative_1():
    # En passant should be blocked when the opposing king occupies the destination square.

    ##    0  1  2  3  4  5  6  7                ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|              ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|bp|##|__|##|__|   prev       ## 1 |##|__|##|__|##|__|##|__|   prev
    ## 2 |__|##|__|bk|__|##|__|##|              ## 2 |__|##|__|__|__|##|__|##|
    ## 3 |##|__|##|bp|wp|__|##|__|   curr       ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|              ## 4 |__|##|__|wp|bp|##|__|##|   curr
    ## 5 |##|__|##|__|##|__|##|__|              ## 5 |##|__|##|wk|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|              ## 6 |__|##|__|wp|__|##|__|##|   prev
    ## 7 |##|__|##|__|##|__|##|__|              ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposing_side = "black" if side == "white" else "white"
        curr_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5
        opposing_start_row = 1 if opposing_side == "black" else 6

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][curr_row][4] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][curr_row][3] = [{"type": f"{opposing_side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposing_side}_king"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][opposing_start_row][3] = [{"type": f"{opposing_side}_pawn"}]
        prev_game_state["board_state"][curr_row][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [curr_row, 4])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert not any(capture[0] == [row_ahead, 3] for capture in result["possible_captures"])


def test_pawn_en_passant_negative_2():
    # En passant should be blocked when the destination square is already occupied.

    ##    0  1  2  3  4  5  6  7                ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|              ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|bp|##|__|##|__|   prev       ## 1 |##|__|##|__|##|__|##|__|   prev
    ## 2 |__|##|__|wp|__|##|__|##|  destination ## 2 |__|##|__|__|__|##|__|##|
    ## 3 |##|__|##|bp|wp|__|##|__|   curr       ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|              ## 4 |__|##|__|wp|bp|##|__|##|   curr
    ## 5 |##|__|##|__|##|__|##|__|              ## 5 |##|__|##|bp|##|__|##|__|  destination
    ## 6 |__|##|__|##|__|##|__|##|              ## 6 |__|##|__|wp|__|##|__|##|   prev
    ## 7 |##|__|##|__|##|__|##|__|              ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposing_side = "black" if side == "white" else "white"
        curr_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5
        opposing_start_row = 1 if opposing_side == "black" else 6

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][curr_row][4] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][curr_row][3] = [{"type": f"{opposing_side}_pawn"}]
        # Destination square is occupied by a friendly pawn
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][opposing_start_row][3] = [{"type": f"{opposing_side}_pawn"}]
        prev_game_state["board_state"][curr_row][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [curr_row, 4])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert not any(capture[0] == [row_ahead, 3] for capture in result["possible_captures"])


def test_pawn_capturing_adjacent_bishop():
    ##    0  1  2  3  4  5  6  7        ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|      ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|bb|__|##|__|      ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|bp|##|__|##|      ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|      ## 3 |##|__|##|bk|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|      ## 4 |__|##|__|##|wp|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|      ## 5 |##|__|##|__|wb|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|      ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|      ## 7 |##|__|##|__|##|__|##|__|
    
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][3][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][2 if side == 'white' else 4][4] = [{"type": f"{opposite_side}_pawn"}]
        curr_game_state["board_state"][1 if side == 'white' else 5][4] = [{"type": f"{opposite_side}_bishop"}]

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, None, [3, 3])

        # moving to [2, 4] would allow the capturing of [2, 4] and [1, 4]
        # moving to [2, 3] would allow the capturing of [1, 4]
        assert sorted(possible_moves_and_captures["possible_captures"]) == sorted([
            [
                [2, 4] if side == 'white' else [4, 4], 
                [2, 4] if side == 'white' else [4, 4]
            ], 
            [
                [2, 4] if side == 'white' else [4, 4],
                [1, 4] if side == 'white' else [5, 4]
            ], 
            [
                [2, 3] if side == 'white' else [4, 3], 
                [1, 4] if side == 'white' else [5, 4]
            ]
        ])


def test_pawn_not_being_allowed_to_move_to_sword_in_stone_square():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|ss|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp|##|__|##|__|
    ## 4 |__|##|__|ss|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    for side in ["white", "black"]:
        for sword_in_the_stone_position in ([[2, 2], [2, 3], [2, 4]] if side == 'white' else [[4, 2], [4, 3], [4, 4]]):
            curr_game_state = copy.deepcopy(empty_game)
            curr_game_state["turn_count"] = 0
            curr_game_state["board_state"][3][3] = [{"type": f"{side}_pawn"}]
            curr_game_state["sword_in_the_stone_position"] = sword_in_the_stone_position

            prev_game_state = copy.deepcopy(curr_game_state)
            curr_position = [3, 3]

            possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)
            assert sword_in_the_stone_position not in possible_moves_and_captures["possible_moves"]


def test_pawn_threatening_move():
    ##    0  1  2  3  4  5  6  7        ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|      ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|      ## 1 |##|__|##|__|##|__|##|__| 
    ## 2 |__|##|__|##|__|##|__|##|      ## 2 |__|##|__|##|bK|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|      ## 3 |##|__|##|wp|__|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|      ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|      ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|      ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|      ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7        ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|      ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|      ## 1 |##|__|##|__|##|__|##|__| 
    ## 2 |__|##|__|##|__|##|__|##|      ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp|##|__|##|__|      ## 3 |##|__|##|bp|__|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|      ## 4 |__|##|__|##|wK|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|      ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|      ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|      ## 7 |##|__|##|__|##|__|##|__|
    
    for side in ["white", "black"]:
        opposite_side = "white" if side == "black" else "black"
        if side == 'white':
            king_positions = [[None, None], [2, 2], [2, 4]]
        else:
            king_positions = [[None, None], [4, 2], [4, 4]]

        for king_position in king_positions:
            curr_game_state = copy.deepcopy(empty_game)
            curr_game_state["board_state"][3][3] = [{"type": f"{side}_pawn"}]
            if king_position[0] is not None:
                curr_game_state["board_state"][king_position[0]][king_position[1]] = [{"type": f"{opposite_side}_king"}]

            prev_game_state = copy.deepcopy(curr_game_state)

            curr_position = [3, 3]

            possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, curr_position)

            assert [king_position, king_position] not in possible_moves_and_captures["possible_captures"]
            assert len(possible_moves_and_captures["possible_captures"]) == 0
            if king_position[0] is not None:
                assert [king_position] == possible_moves_and_captures["threatening_move"]
            else:
                assert [king_position] not in possible_moves_and_captures["threatening_move"]
                assert len(possible_moves_and_captures["threatening_move"]) == 0

def test_pawn_forward_capture_when_average_piece_value_is_at_least_two_points_higher():
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        row_ahead = 3 if side == 'white' else 4
        attacker_row = 2 if side == 'white' else 5

        # Case A: attacker pawn_buff=2, enemy pawn pawn_buff=0 → forward capture is available
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{side}_pawn", "pawn_buff": 0}]
        curr_game_state["board_state"][attacker_row][3] = [{"type": f"{opposite_side}_pawn", "pawn_buff": 2}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == 'white' else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [attacker_row, 3])

        assert [row_ahead, 3] in possible_moves_and_captures["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] in possible_moves_and_captures["possible_captures"]

        # Case B: attacker pawn_buff=0 (no advantage) → forward capture is not available
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{side}_pawn", "pawn_buff": 0}]
        curr_game_state["board_state"][attacker_row][3] = [{"type": f"{opposite_side}_pawn", "pawn_buff": 0}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == 'white' else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [attacker_row, 3])

        assert len(possible_moves_and_captures["possible_moves"]) == 0
        assert len(possible_moves_and_captures["possible_captures"]) == 0


def test_pawn_immunity_when_average_piece_value_is_at_least_three_points_higher():
    ## Case A: immune pawn only          Case B: immune pawn + capturable knight
    ##    0  1  2  3  4  5  6  7        ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|      ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|      ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|      ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|wp|__|##|__|##|__|      ## 3 |##|__|wp|__|wk|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|      ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|      ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|      ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|      ## 7 |##|__|##|__|##|__|##|__|
    ## wp=immune(pawn_buff=3)           ## wp=immune(pawn_buff=3), wk=capturable

    ##    0  1  2  3  4  5  6  7        ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|      ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|      ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|      ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|      ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|bp|##|__|##|__|##|      ## 4 |__|##|bp|##|bk|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|      ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|      ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|      ## 7 |##|__|##|__|##|__|##|__|
    ## bp=immune(pawn_buff=3)           ## bp=immune(pawn_buff=3), bk=capturable

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        row_ahead = 3 if side == 'white' else 4
        attacker_row = 2 if side == 'white' else 5

        # Case A: immune pawn (pawn_buff=3) in diagonal — attacker cannot capture it
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][row_ahead][2] = [{"type": f"{side}_pawn", "pawn_buff": 3}]
        curr_game_state["board_state"][attacker_row][3] = [{"type": f"{opposite_side}_pawn", "pawn_buff": 0}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == 'white' else -1)][2] = copy.deepcopy(curr_game_state["board_state"][row_ahead][2])
        prev_game_state["board_state"][row_ahead][2] = None

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [attacker_row, 3])

        assert len(possible_moves_and_captures["possible_captures"]) == 0
        assert [row_ahead, 3] in possible_moves_and_captures["possible_moves"]

        # Case B: immune pawn at [row_ahead][2], non-immune knight at [row_ahead][4] — knight IS capturable, immune pawn is not
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][row_ahead][2] = [{"type": f"{side}_pawn", "pawn_buff": 3}]
        curr_game_state["board_state"][row_ahead][4] = [{"type": f"{side}_knight"}]
        curr_game_state["board_state"][attacker_row][3] = [{"type": f"{opposite_side}_pawn", "pawn_buff": 0}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == 'white' else -1)][2] = copy.deepcopy(curr_game_state["board_state"][row_ahead][2])
        prev_game_state["board_state"][row_ahead][2] = None

        possible_moves_and_captures = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [attacker_row, 3])

        assert [[row_ahead, 4], [row_ahead, 4]] in possible_moves_and_captures["possible_captures"]
        assert [[row_ahead, 2], [row_ahead, 2]] not in possible_moves_and_captures["possible_captures"]

def test_board_herald_buff_enables_pawn_forward_capture():
    ## Case A: ally w/ herald buff adjacent  Case B: ally WITHOUT herald buff (negative)
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|          ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|wp|wr*|__|##|__|         ## 3 |##|__|##|wp|wr|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wr*=has board_herald_buff            ## wr=no buff → no forward capture

    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|br*|##|__|##|         ## 4 |__|##|__|bp|br|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|          ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## br*=has board_herald_buff            ## br=no buff → no forward capture

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: ally piece with board_herald_buff adjacent → forward capture enabled
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn"}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook", "board_herald_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] in result["possible_captures"]

        # Case B: ally piece WITHOUT board_herald_buff → no forward capture
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn"}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]


def test_board_herald_buff_enables_pawn_forward_check():
    ## Case A: ally w/ herald buff adjacent  Case B: ally WITHOUT herald buff (negative)
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bK|__|##|__|##|          ## 2 |__|##|__|bK|__|##|__|##|
    ## 3 |##|__|##|wp|wr*|__|##|__|         ## 3 |##|__|##|wp|wr|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wr*=has board_herald_buff            ## wr=no buff → no forward check

    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|br*|##|__|##|         ## 4 |__|##|__|bp|br|##|__|##|
    ## 5 |##|__|##|wK|##|__|##|__|          ## 5 |##|__|##|wK|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## br*=has board_herald_buff            ## br=no buff → no forward check

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: ally piece with board_herald_buff adjacent → forward check on enemy king
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_king"}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook", "board_herald_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] in result["threatening_move"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]

        # Case B: ally piece WITHOUT board_herald_buff → no forward check
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_king"}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["threatening_move"]


def test_baron_nashor_buff_enables_forward_capture():
    ## Case A: pawn w/ baron buff            Case B: pawn WITHOUT baron buff (negative)
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|          ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|wp*|__|##|__|##|         ## 3 |##|__|##|wp|__|##|__|##|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wp*=has baron_nashor_buff            ## wp=no buff → no forward capture

    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp*|__|##|__|##|         ## 4 |__|##|__|bp|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|          ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## bp*=has baron_nashor_buff            ## bp=no buff → no forward capture

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: pawn with baron_nashor_buff → forward capture enabled
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "baron_nashor_buff": True}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] in result["possible_captures"]

        # Case B: pawn WITHOUT baron_nashor_buff → no forward capture
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]


def test_baron_nashor_buff_enables_forward_check():
    ## Case A: pawn w/ baron buff            Case B: pawn WITHOUT baron buff (negative)
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bK|__|##|__|##|          ## 2 |__|##|__|bK|__|##|__|##|
    ## 3 |##|__|##|wp*|__|##|__|##|         ## 3 |##|__|##|wp|__|##|__|##|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wp*=has baron_nashor_buff            ## wp=no buff → no forward check

    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp*|__|##|__|##|         ## 4 |__|##|__|bp|__|##|__|##|
    ## 5 |##|__|##|wK|##|__|##|__|          ## 5 |##|__|##|wK|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## bp*=has baron_nashor_buff            ## bp=no buff → no forward check

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: pawn with baron_nashor_buff → forward check on enemy king
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "baron_nashor_buff": True}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_king"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] in result["threatening_move"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]

        # Case B: pawn WITHOUT baron_nashor_buff → no forward check
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_king"}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][row_ahead + (1 if side == "white" else -1)][3] = copy.deepcopy(curr_game_state["board_state"][row_ahead][3])
        prev_game_state["board_state"][row_ahead][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["threatening_move"]


def test_baron_nashor_buff_prevents_pawn_capture():
    ## Case A: diagonal blocked              Case B: forward (pawn_buff) blocked
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|bp*|##|__|##|__|##|         ## 2 |__|##|__|bp*|__|##|__|##|
    ## 3 |##|__|##|wp|##|__|##|__|          ## 3 |##|__|##|wp|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## bp*=baron buff, wp=no baron          ## bp*=baron buff, wp has pawn_buff=1
    ##
    ## Case C: forward (herald) blocked      Case D: en passant blocked
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|bp*|##|__|##|__|  prev
    ## 2 |__|##|__|bp*|__|##|__|##|         ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|wp|wr^|__|##|__|         ## 3 |##|__|##|bp*|wp|__|##|__|  curr
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## bp*=baron buff, wr^=herald buff      ## bp*=baron buff, wp=no baron
    ##
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|__|##|__|##|          ## 4 |__|##|__|bp|__|##|__|##|
    ## 5 |##|__|wp*|##|__|##|__|##|         ## 5 |##|__|##|wp*|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wp*=baron buff, bp=no baron          ## wp*=baron buff, bp has pawn_buff=1
    ##
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp|br^|##|__|##|         ## 4 |__|##|__|wp*|bp|__|##|__|  curr
    ## 5 |##|__|##|wp*|##|__|##|__|         ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|wp*|__|##|__|##|  prev
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## wp*=baron buff, br^=herald buff      ## wp*=baron buff, bp=no baron

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: diagonal capture blocked — target pawn has baron buff, attacker has no baron
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][2] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 2] not in result["possible_moves"]
        assert [[row_ahead, 2], [row_ahead, 2]] not in result["possible_captures"]

        # Case B: forward capture via pawn_buff blocked — target pawn has baron buff
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "pawn_buff": 1}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]

        # Case C: forward capture via board_herald blocked — target pawn has baron buff
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook", "board_herald_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]

        # Case D: en passant blocked — target pawn has baron buff
        opposing_start_row = 1 if opposite_side == "black" else 6

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)
        prev_game_state["board_state"][opposing_start_row][3] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]
        prev_game_state["board_state"][pawn_row][3] = None

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 4])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [pawn_row, 3]] not in result["possible_captures"]


def test_baron_nashor_buff_negates_baron_nashor_buff_forward_capture():
    ## Case A: both barons → no fwd capture  Case B: both barons → diagonal capture works
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp*|__|##|__|##|         ## 2 |__|##|bp*|##|__|##|__|##|
    ## 3 |##|__|##|wp*|##|__|##|__|         ## 3 |##|__|##|wp*|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|          ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|          ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## both *=baron buff                    ## both *=baron buff
    ##
    ##    0  1  2  3  4  5  6  7            ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|          ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|          ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|          ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|          ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|bp*|__|##|__|##|         ## 4 |__|##|__|bp*|__|##|__|##|
    ## 5 |##|__|##|wp*|##|__|##|__|         ## 5 |##|__|wp*|##|__|##|__|##|
    ## 6 |__|##|__|##|__|##|__|##|          ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|          ## 7 |##|__|##|__|##|__|##|__|
    ## both *=baron buff                    ## both *=baron buff

    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 3 if side == "white" else 4
        row_ahead = 2 if side == "white" else 5

        # Case A: both pawns have baron buff → forward capture blocked (buffs cancel)
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "baron_nashor_buff": True}]
        curr_game_state["board_state"][row_ahead][3] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 3] not in result["possible_moves"]
        assert [[row_ahead, 3], [row_ahead, 3]] not in result["possible_captures"]

        # Case B: both pawns have baron buff → diagonal capture works (immunity negated)
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "baron_nashor_buff": True}]
        curr_game_state["board_state"][row_ahead][2] = [{"type": f"{opposite_side}_pawn", "baron_nashor_buff": True}]

        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_ahead, 2] in result["possible_moves"]
        assert [[row_ahead, 2], [row_ahead, 2]] in result["possible_captures"]

def test_pawn_extended_movement_with_one_or_more_dragon_buff_stacks():
    ## Case A: dragon_buff=1, pawn moves 2 squares forward
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=1
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=1
    for side in ["white", "black"]:
        pawn_row = 4 if side == "white" else 3
        modifier = -1 if side == "white" else 1

        # Case A (positive): dragon_buff=1 → can move 1 and 2 squares forward
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + modifier, 3] in result["possible_moves"]
        assert [pawn_row + 2*modifier, 3] in result["possible_moves"]

        # Case B (negative): dragon_buff=0 → can only move 1 square forward
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 0}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + modifier, 3] in result["possible_moves"]
        assert [pawn_row + 2*modifier, 3] not in result["possible_moves"]


def test_pawn_extended_diagonal_capture_with_one_or_more_dragon_buff_stacks():
    ## Case A: dragon_buff=1, diagonal capture at distance 2
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|bp|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=1
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|wp|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=1
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 4 if side == "white" else 3
        modifier = -1 if side == "white" else 1
        diag_row = pawn_row + 2*modifier
        diag_col = 1

        # Case A (positive): dragon_buff=1, enemy at diagonal distance 2, intermediate clear
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        curr_game_state["board_state"][diag_row][diag_col] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [diag_row, diag_col] in result["possible_moves"]
        assert [[diag_row, diag_col], [diag_row, diag_col]] in result["possible_captures"]

        # Case B (negative): dragon_buff=0, enemy at diagonal distance 2 → no capture
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 0}]
        curr_game_state["board_state"][diag_row][diag_col] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [diag_row, diag_col] not in result["possible_moves"]
        assert [[diag_row, diag_col], [diag_row, diag_col]] not in result["possible_captures"]


def test_pawn_forward_capture_extended_range_with_one_or_more_dragon_buff_stacks():
    ## Case A: pawn_buff=1 forward capture at distance 2
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=1, pawn_buff=1
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=1, pawn_buff=1
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        pawn_row = 4 if side == "white" else 3
        modifier = -1 if side == "white" else 1
        row_2_ahead = pawn_row + 2*modifier

        # Case A: pawn_buff=1 + dragon_buff=1 → forward capture at distance 2
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1, "pawn_buff": 1}]
        curr_game_state["board_state"][row_2_ahead][3] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_2_ahead, 3] in result["possible_moves"]
        assert [[row_2_ahead, 3], [row_2_ahead, 3]] in result["possible_captures"]

        # Case B: board_herald buff + dragon_buff=1 → forward capture at distance 2
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        curr_game_state["board_state"][row_2_ahead][3] = [{"type": f"{opposite_side}_pawn"}]
        curr_game_state["board_state"][pawn_row][4] = [{"type": f"{side}_rook", "board_herald_buff": True}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_2_ahead, 3] in result["possible_moves"]
        assert [[row_2_ahead, 3], [row_2_ahead, 3]] in result["possible_captures"]

        # Case C: baron_nashor_buff + dragon_buff=1 → forward capture at distance 2
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1, "baron_nashor_buff": True}]
        curr_game_state["board_state"][row_2_ahead][3] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [row_2_ahead, 3] in result["possible_moves"]
        assert [[row_2_ahead, 3], [row_2_ahead, 3]] in result["possible_captures"]


def test_pawn_with_three_or_more_dragon_buff_stacks_ignores_unit_collision_with_ally_pawns():
    ## Case A: starting square, ally pawn 1 ahead, can move 2 ahead (over ally pawn)
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|wp|##|__|##|__|
    ## 6 |__|##|__|wp^|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=3
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|bp^|##|__|##|__|
    ## 2 |__|##|__|bp|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=3
    for side in ["white", "black"]:
        modifier = -1 if side == "white" else 1
        starting_row = 6 if side == "white" else 1

        # Case A: starting square, ally pawn 1 ahead → can jump over to 2 ahead
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][starting_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][starting_row + modifier][3] = [{"type": f"{side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [starting_row, 3])

        # can't land on ally pawn at distance 1, but can pass through to distance 2
        assert [starting_row + modifier, 3] not in result["possible_moves"]
        assert [starting_row + 2*modifier, 3] in result["possible_moves"]

        # Case B: starting square extra move — ally pawn 1 ahead, can reach 3 ahead (starting bonus)
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][starting_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][starting_row + modifier][3] = [{"type": f"{side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [starting_row, 3])

        assert [starting_row + 3*modifier, 3] in result["possible_moves"]

        # Case C: extended movement (non-starting row), ally pawn 1 ahead → can move 2 ahead
        pawn_row = 4 if side == "white" else 3
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + modifier, 3] not in result["possible_moves"]
        assert [pawn_row + 2*modifier, 3] in result["possible_moves"]

        # Case D: extended diagonal capture, ally pawn at intermediate diagonal → can capture at distance 2
        curr_game_state = copy.deepcopy(empty_game)
        opposite_side = "black" if side == "white" else "white"
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][pawn_row + modifier][2] = [{"type": f"{side}_pawn"}]
        curr_game_state["board_state"][pawn_row + 2*modifier][1] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 1] in result["possible_moves"]
        assert [[pawn_row + 2*modifier, 1], [pawn_row + 2*modifier, 1]] in result["possible_captures"]


def test_pawn_with_three_dragon_buff_stacks_does_not_ignore_unit_collision_with_ally_non_pawns():
    ## Ally rook blocks extended movement at dragon_buff=3
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|wr|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=3
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|br|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=3
    for side in ["white", "black"]:
        modifier = -1 if side == "white" else 1
        pawn_row = 4 if side == "white" else 3

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{side}_rook"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 3] not in result["possible_moves"]


def test_pawn_with_three_dragon_buff_stacks_does_not_ignore_unit_collision_with_enemy_pawns():
    ## Enemy pawn blocks extended movement at dragon_buff=3
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=3
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|wp|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=3
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        modifier = -1 if side == "white" else 1
        pawn_row = 4 if side == "white" else 3

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 3] not in result["possible_moves"]


def test_pawn_with_three_dragon_buff_stacks_does_not_ignore_unit_collision_with_enemy_non_pawns():
    ## Enemy rook blocks extended movement at dragon_buff=3
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|br|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=3
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|wr|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=3
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        modifier = -1 if side == "white" else 1
        pawn_row = 4 if side == "white" else 3

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 3}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{opposite_side}_rook"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 3] not in result["possible_moves"]


def test_pawn_with_four_or_more_dragon_buff_stacks_ignores_unit_collision_with_ally_pieces():
    ## Case A: ally rook in forward path, can move through at dragon_buff=4
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|wr|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=4
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|br|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=4
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        modifier = -1 if side == "white" else 1

        # Case A: forward movement through ally rook
        pawn_row = 4 if side == "white" else 3
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{side}_rook"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + modifier, 3] not in result["possible_moves"]
        assert [pawn_row + 2*modifier, 3] in result["possible_moves"]

        # Case B: starting square, ally knight 1 ahead → can jump to 2 ahead
        starting_row = 6 if side == "white" else 1
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][starting_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        curr_game_state["board_state"][starting_row + modifier][3] = [{"type": f"{side}_knight"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [starting_row, 3])

        assert [starting_row + modifier, 3] not in result["possible_moves"]
        assert [starting_row + 2*modifier, 3] in result["possible_moves"]

        # Case C: starting square extra move — ally bishop 1 ahead, can reach 3 ahead
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][starting_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        curr_game_state["board_state"][starting_row + modifier][3] = [{"type": f"{side}_bishop"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [starting_row, 3])

        assert [starting_row + 3*modifier, 3] in result["possible_moves"]

        # Case D: extended diagonal, ally rook at intermediate → can capture enemy at distance 2
        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        curr_game_state["board_state"][pawn_row + modifier][2] = [{"type": f"{side}_rook"}]
        curr_game_state["board_state"][pawn_row + 2*modifier][1] = [{"type": f"{opposite_side}_pawn"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 1] in result["possible_moves"]
        assert [[pawn_row + 2*modifier, 1], [pawn_row + 2*modifier, 1]] in result["possible_captures"]


def test_pawn_with_four_or_more_dragon_buff_stacks_does_not_ignore_unit_collision_with_enemy_pieces():
    ## Enemy rook blocks extended movement at dragon_buff=4
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|br|##|__|##|__|
    ## 4 |__|##|__|wp^|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=4
    ##
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|bp^|##|__|##|__|
    ## 4 |__|##|__|wr|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|##|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## bp^=dragon_buff=4
    for side in ["white", "black"]:
        opposite_side = "black" if side == "white" else "white"
        modifier = -1 if side == "white" else 1
        pawn_row = 4 if side == "white" else 3

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][pawn_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 4}]
        curr_game_state["board_state"][pawn_row + modifier][3] = [{"type": f"{opposite_side}_rook"}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [pawn_row, 3])

        assert [pawn_row + 2*modifier, 3] not in result["possible_moves"]


def test_pawn_with_dragon_buff_on_starting_row_has_no_duplicate_possible_moves():
    ## Regression: dragon_buff=1 pawn on starting row produced [row-2, col] twice
    ## (once from starting-row two-square logic and once from dragon extended range)
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|##|__|##|__|##|__|##|
    ## 1 |##|__|##|__|##|__|##|__|
    ## 2 |__|##|__|##|__|##|__|##|
    ## 3 |##|__|##|__|##|__|##|__|
    ## 4 |__|##|__|##|__|##|__|##|
    ## 5 |##|__|##|__|##|__|##|__|
    ## 6 |__|##|__|wp^|__|##|__|##|
    ## 7 |##|__|##|__|##|__|##|__|
    ## wp^=dragon_buff=1
    for side in ["white", "black"]:
        starting_row = 6 if side == "white" else 1
        modifier = -1 if side == "white" else 1

        curr_game_state = copy.deepcopy(empty_game)
        curr_game_state["board_state"][starting_row][3] = [{"type": f"{side}_pawn", "dragon_buff": 1}]
        prev_game_state = copy.deepcopy(curr_game_state)

        result = moves.get_moves_for_pawn(curr_game_state, prev_game_state, [starting_row, 3])

        two_ahead = [starting_row + 2*modifier, 3]
        assert two_ahead in result["possible_moves"]
        assert result["possible_moves"].count(two_ahead) == 1, \
            f"Duplicate move {two_ahead} in possible_moves: {result['possible_moves']}"
