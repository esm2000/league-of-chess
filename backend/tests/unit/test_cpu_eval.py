"""Unit tests for the CPU static evaluation."""

import copy

from mocks.empty_game import empty_game
from mocks.starting_game import starting_game
from src.cpu_eval import MATE_SCORE, evaluate, get_material_value, get_rook_range


def _make_game(**overrides):
    """Empty board with both kings on their home squares."""
    game = copy.deepcopy(empty_game)
    game["board_state"][0][4] = [{"type": "black_king"}]
    game["board_state"][7][4] = [{"type": "white_king"}]
    for key, value in overrides.items():
        game[key] = value
    return game


def _with_pawns(game):
    """Add one pawn per side so the position is not a kings-only draw."""
    game["board_state"][1][0] = [{"type": "black_pawn", "pawn_buff": 0}]
    game["board_state"][6][0] = [{"type": "white_pawn", "pawn_buff": 0}]
    return game


def test_evaluate_is_antisymmetric():
    game = copy.deepcopy(starting_game)
    assert evaluate(game, "black") == -evaluate(game, "white")


def test_mirrored_position_is_even():
    game = _with_pawns(_make_game())
    assert evaluate(game, "black") == 0


def test_extra_material_scores_higher():
    game = _with_pawns(_make_game())
    baseline = evaluate(game, "black")
    game["board_state"][2][3] = [{"type": "black_knight"}]
    assert evaluate(game, "black") > baseline + 200


def test_defeat_flags_are_terminal_scores():
    game = _with_pawns(_make_game())
    assert evaluate({**game, "white_defeat": True}, "black") == MATE_SCORE
    assert evaluate({**game, "black_defeat": True}, "black") == -MATE_SCORE
    assert evaluate({**game, "black_defeat": True}, "white") == MATE_SCORE
    assert evaluate({**game, "black_defeat": True, "white_defeat": True}, "black") == 0


def test_only_kings_is_a_draw():
    game = _make_game()
    game["gold_count"] = {"white": 0, "black": 9}
    assert evaluate(game, "black") == 0


def test_rook_value_grows_with_range():
    assert get_rook_range(0) == 3
    assert get_rook_range(15) == 4
    assert get_rook_range(30) == 7
    assert get_rook_range(200) == 7
    assert get_material_value("black_rook", 30) > get_material_value("black_rook", 0)


def test_gold_counts():
    game = _with_pawns(_make_game())
    game["gold_count"] = {"white": 0, "black": 4}
    assert evaluate(game, "black") > 0


def test_piece_doomed_in_monster_zone_is_penalised():
    """A knight that cannot leave the dragon's zone before its kill mark fires is nearly lost."""
    game = _with_pawns(_make_game(turn_count=12))
    game["board_state"][4][7] = [{"type": "neutral_dragon", "health": 5, "turn_spawned": 10}]
    game["board_state"][3][6] = [{"type": "black_knight", "neutral_kill_mark": 13}]
    doomed = evaluate(game, "black")

    # Same knight with a mark far enough out that black still gets a move first
    game["board_state"][3][6] = [{"type": "black_knight", "neutral_kill_mark": 14}]
    escapable = evaluate(game, "black")

    assert escapable - doomed > 150


def test_piece_on_upcoming_spawn_square_is_penalised():
    game = _with_pawns(_make_game(turn_count=9))
    game["board_state"][2][2] = [{"type": "black_knight"}]
    safe = evaluate(game, "black")
    game["board_state"][2][2] = None
    game["board_state"][4][7] = [{"type": "black_knight"}]
    assert evaluate(game, "black") < safe - 150


def test_monster_buffs_raise_owner_score():
    game = _with_pawns(_make_game())
    baseline = evaluate(game, "black")

    with_dragon = copy.deepcopy(game)
    with_dragon["neutral_buff_log"]["black"]["dragon"] = {"stacks": 2, "turn": 12}
    assert evaluate(with_dragon, "black") > baseline

    more_dragon = copy.deepcopy(game)
    more_dragon["neutral_buff_log"]["black"]["dragon"] = {"stacks": 5, "turn": 12}
    assert evaluate(more_dragon, "black") > evaluate(with_dragon, "black")

    with_herald = copy.deepcopy(game)
    with_herald["neutral_buff_log"]["black"]["board_herald"] = {"active": True, "turn": 12}
    assert evaluate(with_herald, "black") > baseline

    with_baron = copy.deepcopy(game)
    with_baron["neutral_buff_log"]["white"]["baron_nashor"] = {"active": True, "turn": 36}
    assert evaluate(with_baron, "black") < baseline


def test_statuses_lower_piece_value():
    game = _with_pawns(_make_game())
    game["board_state"][2][3] = [{"type": "black_knight"}]
    healthy = evaluate(game, "black")

    game["board_state"][2][3] = [{"type": "black_knight", "is_stunned": True, "turn_stunned_for": 1}]
    assert evaluate(game, "black") < healthy

    game["board_state"][2][3] = [{"type": "black_knight", "bishop_debuff": 3}]
    assert evaluate(game, "black") < healthy - 150


def test_marked_for_death_costs_the_cheapest_marked_piece():
    game = _with_pawns(_make_game())
    game["board_state"][2][3] = [{"type": "black_knight"}]
    game["board_state"][2][4] = [{"type": "black_rook"}]
    unmarked = evaluate(game, "black")
    game["board_state"][2][3][0]["marked_for_death"] = True
    game["board_state"][2][4][0]["marked_for_death"] = True
    assert unmarked - evaluate(game, "black") == get_material_value("black_knight")


def test_capture_point_advantage_counts_for_holder():
    game = _with_pawns(_make_game())
    game["capture_point_advantage"] = ["black", 1.5]
    assert evaluate(game, "black") > 0
    game["capture_point_advantage"] = ["white", 1.5]
    assert evaluate(game, "black") < 0
