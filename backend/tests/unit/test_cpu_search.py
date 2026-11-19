"""Unit tests for the CPU lookahead search."""

import copy
import time

from mocks.empty_game import empty_game
from src.cpu_search import (
    apply_action,
    choose_action,
    get_board_actions,
    get_forced_action,
    get_purchase_actions,
    get_side_to_move,
    resolve_forced_steps,
)

# Small budgets keep the suite fast; these positions are tiny.
TIME_LIMIT = 2.0


def _make_game(turn_count=1, **overrides):
    """Empty board with both kings on their home squares, black to move by default."""
    game = copy.deepcopy(empty_game)
    game["turn_count"] = turn_count
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]
    for key, value in overrides.items():
        game[key] = value
    return game


def _finish(game):
    game["previous_state"] = copy.deepcopy(game)
    return game


def test_side_to_move_follows_turn_parity():
    assert get_side_to_move(_make_game(turn_count=4)) == "white"
    assert get_side_to_move(_make_game(turn_count=5)) == "black"


def test_apply_action_does_not_modify_input():
    game = _make_game()
    game["board_state"][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)
    snapshot = copy.deepcopy(game)

    result = apply_action(game, {"type": "move", "from_pos": [1, 0], "to_pos": [2, 0]}, "black")

    assert game == snapshot
    assert result["turn_count"] == 2
    assert result["board_state"][2][0][0]["type"] == "black_pawn"
    assert result["latest_movement"]["record"][0]["current_position"] == [2, 0]


def test_apply_action_rejects_move_into_check():
    game = _make_game()
    game["board_state"][7][3] = [{"type": "white_rook"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    # The rook covers the d-file up to its range; d8 is attacked only if in range,
    # so use the square next to the white king instead.
    game["board_state"][0][4] = None
    game["board_state"][5][3] = [{"type": "black_king"}]
    _finish(game)
    assert apply_action(game, {"type": "move", "from_pos": [5, 3], "to_pos": [6, 3]}, "black") is None


def test_takes_hanging_queen():
    game = _make_game()
    game["board_state"][2][2] = [{"type": "black_knight"}]
    game["board_state"][4][1] = [{"type": "white_queen"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    action = choose_action(game, time_limit=TIME_LIMIT)

    assert action["type"] == "capture"
    assert action["capture_at"] == [4, 1]


def test_does_not_trade_rook_for_defended_pawn():
    game = _make_game()
    game["board_state"][2][3] = [{"type": "black_rook"}]
    game["board_state"][5][3] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][6][4] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][6][2] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    assert {"type": "capture", "from_pos": [2, 3], "to_pos": [5, 3], "capture_at": [5, 3]} in get_board_actions(game, "black")

    action = choose_action(game, time_limit=TIME_LIMIT)

    assert not (action["type"] == "capture" and action["capture_at"] == [5, 3])


def test_queen_uses_kill_reset_to_take_defended_pawn_safely():
    """A queen capture grants an extra queen move, so taking a defended pawn is safe."""
    game = _make_game()
    game["board_state"][1][3] = [{"type": "black_queen"}]
    game["board_state"][5][3] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][6][4] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][6][2] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    action = choose_action(game, time_limit=TIME_LIMIT)
    assert action["type"] == "capture" and action["capture_at"] == [5, 3]

    after_capture = apply_action(game, action, "black")
    assert after_capture["queen_reset"] is True
    assert get_side_to_move(after_capture) == "black"


def test_finds_mate_in_one():
    """White king boxed into the corner by its own pawns; the queen mates on the back rank."""
    game = _make_game()
    game["board_state"][7][4] = None
    game["board_state"][7][7] = [{"type": "white_king"}]
    game["board_state"][6][6] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][6][7] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][2][0] = [{"type": "black_queen"}]
    _finish(game)

    action = choose_action(game, time_limit=TIME_LIMIT)
    result = apply_action(game, action, "black")

    assert result["white_defeat"] is True
    assert result["black_defeat"] is False


def test_takes_one_health_dragon():
    game = _make_game(turn_count=11)
    game["board_state"][4][7] = [{"type": "neutral_dragon", "health": 1, "turn_spawned": 10}]
    game["board_state"][2][6] = [{"type": "black_knight"}]
    game["board_state"][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    action = choose_action(game, time_limit=TIME_LIMIT)

    assert action["type"] == "capture"
    assert action["capture_at"] == [4, 7]


def test_moves_piece_out_of_monster_zone_before_it_dies():
    """A queen whose kill mark fires next turn must leave the dragon's zone now."""
    game = _make_game(turn_count=13)
    game["board_state"][4][7] = [{"type": "neutral_dragon", "health": 5, "turn_spawned": 10}]
    game["board_state"][3][6] = [{"type": "black_queen", "neutral_kill_mark": 14}]
    game["board_state"][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["neutral_attack_log"] = {"neutral_dragon": {"turn": 12}}
    _finish(game)

    action = choose_action(game, time_limit=TIME_LIMIT)

    assert action["from_pos"] == [3, 6]
    to_row, to_col = action["to_pos"]
    assert abs(to_row - 4) > 1 or abs(to_col - 7) > 1


def test_buffed_pawn_moves_are_searched():
    """Dragon-buffed pawns reach two squares, including a two-square diagonal capture."""
    game = _make_game()
    game["board_state"][3][3] = [{"type": "black_pawn", "pawn_buff": 0, "dragon_buff": 1}]
    game["board_state"][5][5] = [{"type": "white_rook"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    pawn_actions = [a for a in get_board_actions(game, "black") if a["from_pos"] == [3, 3]]
    destinations = {(a["type"], tuple(a["to_pos"])) for a in pawn_actions}
    assert ("move", (5, 3)) in destinations
    assert ("capture", (5, 5)) in destinations
    # Captures are ordered first
    assert get_board_actions(game, "black")[0]["type"] == "capture"

    action = choose_action(game, time_limit=TIME_LIMIT)
    assert action["type"] == "capture" and action["capture_at"] == [5, 5]


def test_generates_moves_for_white():
    game = _make_game(turn_count=2)
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    _finish(game)

    actions = get_board_actions(game, "white")
    assert {"type": "move", "from_pos": [6, 0], "to_pos": [5, 0]} in actions
    assert all(a["from_pos"][0] >= 6 for a in actions)

    result = apply_action(game, {"type": "move", "from_pos": [6, 0], "to_pos": [5, 0]}, "white")
    assert result["turn_count"] == 3


def test_respects_time_limit_and_still_returns_a_legal_move():
    game = _make_game()
    for col in range(8):
        game["board_state"][1][col] = [{"type": "black_pawn", "pawn_buff": 0}]
        game["board_state"][6][col] = [{"type": "white_pawn", "pawn_buff": 0}]
    game["board_state"][0][3] = [{"type": "black_queen"}]
    game["board_state"][7][3] = [{"type": "white_queen"}]
    _finish(game)

    started = time.monotonic()
    action = choose_action(game, time_limit=0.05)
    elapsed = time.monotonic() - started

    assert action is not None
    assert apply_action(game, action, "black") is not None
    assert elapsed < 2.0


def test_returns_none_when_no_legal_action():
    game = _make_game()
    game["board_state"][0][4] = None
    game["board_state"][0][0] = [{"type": "black_king"}]
    game["board_state"][7][4] = None
    game["board_state"][2][1] = [{"type": "white_king"}]
    game["board_state"][1][2] = [{"type": "white_queen"}]
    _finish(game)

    assert choose_action(game, time_limit=TIME_LIMIT) is None


def test_reversing_last_move_is_discouraged():
    """With nothing else to separate them, the search avoids shuffling straight back."""
    game = _make_game()
    game["board_state"][3][3] = [{"type": "black_knight"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    for _ in range(5):
        action = choose_action(
            game, time_limit=TIME_LIMIT, max_depth=1,
            last_own_move={"from": [1, 2], "to": [3, 3]},
        )
        assert not (action["from_pos"] == [3, 3] and action["to_pos"] == [1, 2])


def test_purchase_shortlist_is_limited_and_affordable():
    game = _make_game()
    game["gold_count"] = {"white": 0, "black": 6}
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    purchases = get_purchase_actions(game, "black")
    piece_types = [p["piece_type"] for p in purchases]

    assert "black_rook" not in piece_types
    assert set(piece_types) == {"black_pawn", "black_knight", "black_bishop"}
    assert all(piece_types.count(piece_type) <= 2 for piece_type in set(piece_types))
    assert all(p["to_pos"][0] <= 3 for p in purchases)


def test_forced_promotion_resolves_to_queen():
    game = _make_game()
    game["board_state"][6][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][6][7] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    result = apply_action(game, {"type": "move", "from_pos": [6, 0], "to_pos": [7, 0]}, "black")
    assert get_forced_action(result, "black")["type"] == "promote"

    resolved = resolve_forced_steps(result)
    assert resolved["board_state"][7][0][0]["type"] == "black_queen"
    assert get_side_to_move(resolved) == "white"


def test_forced_bishop_debuff_resolves_to_capture():
    game = _make_game()
    game["board_state"][1][1] = [{"type": "black_bishop", "energize_stacks": 0}]
    game["board_state"][5][5] = [{"type": "white_knight", "bishop_debuff": 2}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    result = apply_action(game, {"type": "move", "from_pos": [1, 1], "to_pos": [2, 2]}, "black")
    assert result["board_state"][5][5][0]["bishop_debuff"] == 3
    assert get_side_to_move(result) == "black"
    assert get_forced_action(result, "black")["type"] == "bishop_capture"

    resolved = resolve_forced_steps(result)
    assert resolved["board_state"][5][5] is None
    assert resolved["captured_pieces"]["black"] == ["white_knight"]
    assert get_side_to_move(resolved) == "white"


def test_forced_sacrifice_gives_up_cheapest_marked_piece():
    game = _make_game()
    game["board_state"][2][3] = [{"type": "black_rook", "marked_for_death": True}]
    game["board_state"][2][5] = [{"type": "black_pawn", "pawn_buff": 0, "marked_for_death": True}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    forced = get_forced_action(game, "black")
    assert forced == {"type": "sacrifice", "from_pos": [2, 5], "piece_type": "black_pawn"}

    resolved = resolve_forced_steps(game)
    assert resolved["board_state"][2][5] is None
    assert resolved["board_state"][2][3][0]["type"] == "black_rook"
    assert not resolved["board_state"][2][3][0].get("marked_for_death")


def test_sacrifice_next_to_empty_monster_square_is_accepted():
    """Surrendering a piece beside a spawn square with no monster on it used to crash the pipeline."""
    game = _make_game()
    game["board_state"][3][6] = [{"type": "black_knight", "marked_for_death": True}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    forced = get_forced_action(game, "black")
    result = apply_action(game, forced, "black")

    assert result is not None
    assert result["board_state"][3][6] is None


def test_stunned_queen_does_not_get_assist_reset():
    """A capture in a stunned queen's reach must not grant a reset she cannot use."""
    game = _make_game()
    game["board_state"][4][7] = [{"type": "black_queen", "is_stunned": True, "turn_stunned_for": 1}]
    game["board_state"][2][4] = [{"type": "black_bishop", "energize_stacks": 0}]
    game["board_state"][4][6] = [{"type": "white_knight"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    capture = {"type": "capture", "from_pos": [2, 4], "to_pos": [4, 6], "capture_at": [4, 6]}
    result = apply_action(game, capture, "black")

    assert result["queen_reset"] is False
    assert get_side_to_move(result) == "white"


def test_unstunned_queen_still_gets_assist_reset():
    game = _make_game()
    game["board_state"][4][7] = [{"type": "black_queen"}]
    game["board_state"][2][4] = [{"type": "black_bishop", "energize_stacks": 0}]
    game["board_state"][4][6] = [{"type": "white_knight"}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    _finish(game)

    capture = {"type": "capture", "from_pos": [2, 4], "to_pos": [4, 6], "capture_at": [4, 6]}
    result = apply_action(game, capture, "black")

    assert result["queen_reset"] is True
    assert result["queen_reset_type"] == "assist"
    assert get_side_to_move(result) == "black"
