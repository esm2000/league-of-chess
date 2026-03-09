"""Type definitions for League of Chess game state and related structures."""

from __future__ import annotations

import datetime
from typing import Literal, Optional, TypedDict


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Position = list[int]
"""[row, col] board coordinate, values 0-7."""

BoardState = list[list[Optional[list["Piece"]]]]
"""8x8 grid. Each cell is None (empty) or a list of Piece dicts."""

Side = Literal['white', 'black', 'neutral']
"""'white', 'black', or 'neutral'."""


# ---------------------------------------------------------------------------
# Piece
# ---------------------------------------------------------------------------

class Piece(TypedDict, total=False):
    """A piece on the board. Only 'type' is required."""

    type: str
    # Pawn
    pawn_buff: int
    board_herald_buff: bool
    baron_nashor_buff: bool
    # Bishop
    energize_stacks: int
    bishop_debuff: int
    # King
    check_protection: int
    # Universal buffs/status
    dragon_buff: int
    is_stunned: bool
    turn_stunned_for: int
    marked_for_death: bool
    neutral_kill_mark: int
    # Monster-only
    health: int
    turn_spawned: int


# ---------------------------------------------------------------------------
# Move results
# ---------------------------------------------------------------------------

class MoveResult(TypedDict):
    """Return value of get_moves_for_*() functions in moves.py."""

    possible_moves: list[Position]
    possible_captures: list[list[Position]]
    threatening_move: list[Position]
    castle_moves: list[Position]


# ---------------------------------------------------------------------------
# Bishop special captures
# ---------------------------------------------------------------------------

class BishopSpecialCapture(TypedDict):
    """A pending bishop debuff capture (3-stack instant capture)."""

    position: Position
    type: str


# ---------------------------------------------------------------------------
# Moved piece tracking
# ---------------------------------------------------------------------------

class MovedPiece(TypedDict):
    """Entry in the moved_pieces list from determine_pieces_that_have_moved()."""

    piece: Piece
    side: Side
    previous_position: Position
    current_position: Position


# ---------------------------------------------------------------------------
# Nested game-state structures
# ---------------------------------------------------------------------------

class CastleSideLog(TypedDict):
    has_king_moved: bool
    has_left_rook_moved: bool
    has_right_rook_moved: bool


class CastleLog(TypedDict):
    white: CastleSideLog
    black: CastleSideLog


class SideBool(TypedDict):
    white: bool
    black: bool


class SideInt(TypedDict):
    white: int
    black: int


class SideStrList(TypedDict):
    white: list[str]
    black: list[str]


class DragonBuffLog(TypedDict):
    stacks: int
    turn: int


class TimedBuffLog(TypedDict):
    active: bool
    turn: int


class SideNeutralBuffLog(TypedDict):
    dragon: DragonBuffLog
    # Legacy MongoDB docs may store board_herald/baron_nashor as plain bool
    # instead of TimedBuffLog. monsters.py normalizes these at runtime.
    board_herald: TimedBuffLog
    baron_nashor: TimedBuffLog


class NeutralBuffLog(TypedDict):
    white: SideNeutralBuffLog
    black: SideNeutralBuffLog


class NeutralAttackEntry(TypedDict):
    turn: int


class LatestMovement(TypedDict, total=False):
    turn_count: int
    record: list[MovedPiece]


class UnsafePositions(TypedDict):
    white: list[Position]
    black: list[Position]


# ---------------------------------------------------------------------------
# Top-level GameState
# ---------------------------------------------------------------------------

class GameState(TypedDict, total=False):
    """Full game state dict as persisted in MongoDB and exchanged via API.

    total=False allows partial states in tests and intermediate pipeline steps.
    """

    id: str
    _id: object

    turn_count: int
    position_in_play: Position
    board_state: BoardState
    possible_moves: list[Position]
    possible_captures: list[list[Position]]
    castle_moves: list[Position]
    captured_pieces: SideStrList
    graveyard: list[str]

    black_defeat: bool
    white_defeat: bool
    check: SideBool

    gold_count: SideInt
    capture_point_advantage: Optional[list[str | float]]

    sword_in_the_stone_position: Optional[Position]

    bishop_special_captures: list[BishopSpecialCapture]

    queen_reset: bool

    latest_movement: LatestMovement

    neutral_attack_log: dict[str, NeutralAttackEntry]
    neutral_buff_log: NeutralBuffLog

    castle_log: CastleLog

    previous_state: GameState
    last_updated: datetime.datetime

    # CPU player fields
    cpu_id: Optional[str]
    last_checked_by_cpu: Optional[datetime.datetime]
    version: int


# ---------------------------------------------------------------------------
# Helper result types
# ---------------------------------------------------------------------------

class MonsterInfoEntry(TypedDict):
    position: Position
    max_health: int


class GoldSpent(TypedDict):
    white: int
    black: int


class PawnExchangeStatus(TypedDict):
    white: bool
    black: bool
