import copy
from mocks.empty_game import empty_game
from src.utils.queen_mechanics import reset_queen_turn_on_kill_or_assist


def test_queen_reset_triggers_on_enemy_death_in_range_as_assist():
    """Queen reset should trigger as 'assist' when an enemy piece dies in range but the queen didn't move there."""
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|__|__|__|bk|__|__|__|
    ## 3 |__|__|bp|__|__|__|__|__|  <- black pawn killed here (in queen's diagonal)
    ## 5 |__|__|__|__|wq|__|__|__|  <- white queen (didn't move)
    ## 7 |wk|__|__|__|__|__|__|__|

    old_game_state = copy.deepcopy(empty_game)
    old_game_state["turn_count"] = 0  # white's turn
    old_game_state["board_state"][5][4] = [{"type": "white_queen"}]
    old_game_state["board_state"][3][2] = [{"type": "black_pawn"}]
    old_game_state["board_state"][7][0] = [{"type": "white_king"}]
    old_game_state["board_state"][0][4] = [{"type": "black_king"}]

    new_game_state = copy.deepcopy(old_game_state)
    new_game_state["queen_reset"] = False
    new_game_state["queen_reset_type"] = None

    # Another white piece captured the black pawn (queen assisted)
    moved_pieces = [
        {
            "piece": {"type": "black_pawn"},
            "side": "black",
            "previous_position": [3, 2],
            "current_position": [None, None],
        },
        {
            "piece": {"type": "white_rook"},
            "side": "white",
            "previous_position": [3, 7],
            "current_position": [3, 2],
        }
    ]

    should_increment = reset_queen_turn_on_kill_or_assist(
        old_game_state, new_game_state, moved_pieces, True
    )

    assert new_game_state["queen_reset"] is True
    assert new_game_state["queen_reset_type"] == "assist"
    assert should_increment is False


def test_queen_reset_triggers_on_enemy_death_as_kill():
    """Queen reset should trigger as 'kill' when the queen herself captured the enemy piece."""
    ##    0  1  2  3  4  5  6  7
    ## 0 |__|__|__|__|bk|__|__|__|
    ## 3 |__|__|bp|__|__|__|__|__|  <- black pawn killed here by queen
    ## 5 |__|__|__|__|wq|__|__|__|  <- white queen moves to [3, 2]
    ## 7 |wk|__|__|__|__|__|__|__|

    old_game_state = copy.deepcopy(empty_game)
    old_game_state["turn_count"] = 0  # white's turn
    old_game_state["board_state"][5][4] = [{"type": "white_queen"}]
    old_game_state["board_state"][3][2] = [{"type": "black_pawn"}]
    old_game_state["board_state"][7][0] = [{"type": "white_king"}]
    old_game_state["board_state"][0][4] = [{"type": "black_king"}]

    new_game_state = copy.deepcopy(old_game_state)
    new_game_state["queen_reset"] = False
    new_game_state["queen_reset_type"] = None

    # Queen moved to the pawn's position (queen killed)
    moved_pieces = [
        {
            "piece": {"type": "black_pawn"},
            "side": "black",
            "previous_position": [3, 2],
            "current_position": [None, None],
        },
        {
            "piece": {"type": "white_queen"},
            "side": "white",
            "previous_position": [5, 4],
            "current_position": [3, 2],
        }
    ]

    should_increment = reset_queen_turn_on_kill_or_assist(
        old_game_state, new_game_state, moved_pieces, True
    )

    assert new_game_state["queen_reset"] is True
    assert new_game_state["queen_reset_type"] == "kill"
    assert should_increment is False


def test_queen_reset_does_not_trigger_on_friendly_pawn_death_with_dragon_buff():
    """Queen reset must NOT trigger when a friendly pawn dies in range of a dragon-buffed queen.

    With 3+ dragon buff stacks, the queen ignores ally pawn collisions, so friendly
    pawn positions appear in the queen's possible_moves. Before the fix, a friendly
    pawn dying on such a square would incorrectly trigger queen reset.
    """
    ##    0  1  2  3  4  5  6  7
    ## 0 |bk|__|__|__|__|__|__|__|
    ## 3 |__|__|wp|__|__|__|__|__|  <- white pawn dies here (queen sees through it with dragon buff)
    ## 5 |__|__|__|__|wq|__|__|__|  <- white queen with 3 dragon buff stacks
    ## 7 |wk|__|__|__|__|__|__|__|

    old_game_state = copy.deepcopy(empty_game)
    old_game_state["turn_count"] = 0  # white's turn
    old_game_state["board_state"][5][4] = [{"type": "white_queen", "dragon_buff": 3}]
    old_game_state["board_state"][3][2] = [{"type": "white_pawn"}]
    old_game_state["board_state"][7][0] = [{"type": "white_king"}]
    old_game_state["board_state"][0][0] = [{"type": "black_king"}]

    new_game_state = copy.deepcopy(old_game_state)
    new_game_state["queen_reset"] = False
    new_game_state["queen_reset_type"] = None

    # Friendly white pawn was killed (current_position = [None, None])
    moved_pieces = [
        {
            "piece": {"type": "white_pawn"},
            "side": "white",
            "previous_position": [3, 2],
            "current_position": [None, None],
        }
    ]

    should_increment = reset_queen_turn_on_kill_or_assist(
        old_game_state, new_game_state, moved_pieces, True
    )

    # Friendly death should NOT trigger queen reset even with dragon buff
    assert new_game_state["queen_reset"] is False
    assert new_game_state["queen_reset_type"] is None
    assert should_increment is True
