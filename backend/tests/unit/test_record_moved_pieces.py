"""Unit tests for record_moved_pieces_this_turn — latest_movement and latest_spawns."""

import copy

from src.utils.game_state import record_moved_pieces_this_turn


def _make_game_state(turn_count=1, latest_movement=None):
    """Create a minimal game state for testing."""
    state = {
        "turn_count": turn_count,
        "latest_movement": latest_movement or {},
        "latest_spawns": {},
    }
    return state


def _make_moved_piece(piece_type, side, from_pos, to_pos):
    return {
        "piece": {"type": piece_type},
        "side": side,
        "previous_position": from_pos,
        "current_position": to_pos,
    }


class TestRecordMovedPiecesRegularMoves:
    def test_regular_move_updates_latest_movement(self):
        state = _make_game_state(turn_count=5)
        moved = [_make_moved_piece("white_pawn", "white", [6, 3], [4, 3])]

        record_moved_pieces_this_turn(state, moved)

        assert state["latest_movement"]["turn_count"] == 5
        assert len(state["latest_movement"]["record"]) == 1
        assert state["latest_movement"]["record"][0]["current_position"] == [4, 3]

    def test_capture_only_does_not_update_latest_movement(self):
        existing = {"turn_count": 4, "record": [{"piece": {"type": "white_bishop"}, "side": "white", "previous_position": [5, 2], "current_position": [3, 4]}]}
        state = _make_game_state(turn_count=5, latest_movement=copy.deepcopy(existing))
        captured = [_make_moved_piece("black_pawn", "black", [3, 4], [None, None])]

        record_moved_pieces_this_turn(state, captured)

        assert state["latest_movement"]["turn_count"] == 4  # unchanged


class TestRecordMovedPiecesSpawns:
    def test_spawn_only_does_not_overwrite_latest_movement(self):
        """Critical: spawn-only turns must preserve latest_movement for bishop debuff tracking."""
        existing = {"turn_count": 4, "record": [{"piece": {"type": "white_bishop"}, "side": "white", "previous_position": [5, 2], "current_position": [3, 4]}]}
        state = _make_game_state(turn_count=5, latest_movement=copy.deepcopy(existing))
        spawned = [_make_moved_piece("black_pawn", "black", [None, None], [1, 7])]

        record_moved_pieces_this_turn(state, spawned)

        # latest_movement should be preserved from the previous turn
        assert state["latest_movement"]["turn_count"] == 4
        assert state["latest_movement"]["record"][0]["piece"]["type"] == "white_bishop"

    def test_spawn_recorded_in_latest_spawns(self):
        state = _make_game_state(turn_count=5)
        spawned = [_make_moved_piece("black_pawn", "black", [None, None], [1, 7])]

        record_moved_pieces_this_turn(state, spawned)

        assert state["latest_spawns"]["turn_count"] == 5
        assert len(state["latest_spawns"]["record"]) == 1
        assert state["latest_spawns"]["record"][0]["current_position"] == [1, 7]

    def test_no_spawns_clears_latest_spawns(self):
        state = _make_game_state(turn_count=5)
        state["latest_spawns"] = {"turn_count": 4, "record": [{"piece": {"type": "black_pawn"}, "side": "black", "previous_position": [None, None], "current_position": [1, 7]}]}
        moved = [_make_moved_piece("white_pawn", "white", [6, 3], [4, 3])]

        record_moved_pieces_this_turn(state, moved)

        assert state["latest_spawns"] == {}


class TestRecordMovedPiecesMixed:
    def test_move_plus_spawn_updates_both_fields(self):
        state = _make_game_state(turn_count=5)
        moved = [
            _make_moved_piece("white_pawn", "white", [6, 3], [4, 3]),
            _make_moved_piece("black_pawn", "black", [None, None], [1, 7]),
        ]

        record_moved_pieces_this_turn(state, moved)

        # latest_movement has the real move only
        assert state["latest_movement"]["turn_count"] == 5
        assert len(state["latest_movement"]["record"]) == 1
        assert state["latest_movement"]["record"][0]["current_position"] == [4, 3]

        # latest_spawns has the spawn only
        assert state["latest_spawns"]["turn_count"] == 5
        assert len(state["latest_spawns"]["record"]) == 1
        assert state["latest_spawns"]["record"][0]["current_position"] == [1, 7]
