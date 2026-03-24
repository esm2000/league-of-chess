"""Unit tests for replay state selection logic."""

from unittest.mock import MagicMock, patch

from src.utils.game_state import get_replay_states


def _make_snapshot(version, turn_count, game_id="test_game"):
    """Create a minimal snapshot dict for testing."""
    return {
        "_id": f"id_{version}",
        "game_id": game_id,
        "version": version,
        "turn_count": turn_count,
    }


def _mock_collection(snapshots):
    """Create a mock MongoDB collection that returns snapshots sorted by version desc."""
    sorted_snaps = sorted(snapshots, key=lambda s: s["version"], reverse=True)
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=sorted_snaps)
    collection = MagicMock()
    collection.find = MagicMock(return_value=cursor)
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    client = MagicMock()
    client.__getitem__ = MagicMock(return_value=db)
    return client


def test_empty_history():
    """No snapshots → returns empty list."""
    client = _mock_collection([])
    result = get_replay_states("test_game", client)
    assert result == []


def test_single_snapshot():
    """Only 1 snapshot → returns it."""
    snaps = [_make_snapshot(1, 0)]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)
    assert len(result) == 1
    assert result[0]["version"] == 1
    assert "_id" not in result[0]


def test_normal_two_turn_replay():
    """Snapshots with turn_count [0,0,1,1,2,2,3,3,4] → 2 transitions back from 4.

    Walking back from version 9 (turn 4):
    - turn 4 → turn 3: first transition
    - turn 3 → turn 2: second transition → stop
    Returns snapshots from turn_count 2 onward (versions 5-9).
    """
    snaps = [
        _make_snapshot(1, 0),
        _make_snapshot(2, 0),
        _make_snapshot(3, 1),
        _make_snapshot(4, 1),
        _make_snapshot(5, 2),
        _make_snapshot(6, 2),
        _make_snapshot(7, 3),
        _make_snapshot(8, 3),
        _make_snapshot(9, 4),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    assert len(result) == 5
    assert [s["version"] for s in result] == [5, 6, 7, 8, 9]
    assert [s["turn_count"] for s in result] == [2, 2, 3, 3, 4]


def test_queen_reset_repeated_turn_count():
    """Turn 1 has 3 states (queen reset) → all included in replay.

    Snapshots: turn_count [0,0,1,1,1,2,2]
    Walking back from turn 2: turn 2→1 (transition 1), turn 1→0 (transition 2) → stop
    Returns turn 0 onward = all snapshots.
    """
    snaps = [
        _make_snapshot(1, 0),
        _make_snapshot(2, 0),
        _make_snapshot(3, 1),
        _make_snapshot(4, 1),
        _make_snapshot(5, 1),  # queen reset extra state
        _make_snapshot(6, 2),
        _make_snapshot(7, 2),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    assert len(result) == 7
    # All 3 states at turn_count 1 are included
    turn1_states = [s for s in result if s["turn_count"] == 1]
    assert len(turn1_states) == 3


def test_stun_skip_turn_count_jumps_by_two():
    """Turn_count jumps from 4→6 (stun skip) → counts as 1 transition.

    Snapshots: [...,3,3,4,6,6]
    Walking back from turn 6: turn 6→4 (transition 1), turn 4→3 (transition 2) → stop
    Returns snapshots from turn 3 onward.
    """
    snaps = [
        _make_snapshot(1, 1),
        _make_snapshot(2, 1),
        _make_snapshot(3, 2),
        _make_snapshot(4, 2),
        _make_snapshot(5, 3),
        _make_snapshot(6, 3),
        _make_snapshot(7, 4),
        _make_snapshot(8, 6),
        _make_snapshot(9, 6),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    assert len(result) == 5
    assert [s["version"] for s in result] == [5, 6, 7, 8, 9]
    assert [s["turn_count"] for s in result] == [3, 3, 4, 6, 6]


def test_only_one_transition_available():
    """Only 1 turn completed → returns all states (less than 2 transitions)."""
    snaps = [
        _make_snapshot(1, 0),
        _make_snapshot(2, 0),
        _make_snapshot(3, 1),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    assert len(result) == 3
    assert [s["turn_count"] for s in result] == [0, 0, 1]


def test_ids_stripped_from_results():
    """MongoDB _id fields should be removed from returned snapshots."""
    snaps = [_make_snapshot(1, 0), _make_snapshot(2, 1)]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    for snap in result:
        assert "_id" not in snap


def test_results_in_ascending_version_order():
    """Results should be sorted by version ascending regardless of query order."""
    snaps = [
        _make_snapshot(5, 2),
        _make_snapshot(6, 2),
        _make_snapshot(7, 3),
        _make_snapshot(8, 3),
        _make_snapshot(9, 4),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    versions = [s["version"] for s in result]
    assert versions == sorted(versions)


def test_many_extensions_at_same_turn():
    """Multiple marked-for-death surrenders at same turn → all included.

    Snapshots: [0,0,1,1,1,1,1,2] (5 states at turn 1 — mark + 4 surrenders)
    """
    snaps = [
        _make_snapshot(1, 0),
        _make_snapshot(2, 0),
        _make_snapshot(3, 1),
        _make_snapshot(4, 1),
        _make_snapshot(5, 1),
        _make_snapshot(6, 1),
        _make_snapshot(7, 1),
        _make_snapshot(8, 2),
    ]
    client = _mock_collection(snaps)
    result = get_replay_states("test_game", client)

    assert len(result) == 8
    turn1_states = [s for s in result if s["turn_count"] == 1]
    assert len(turn1_states) == 5
