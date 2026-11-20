"""Static evaluation for the CPU player.

Scores a game state in centipawns from one side's point of view using the rules as
implemented in this variant: material with variant piece values, piece-square tables,
piece statuses (stun, bishop debuff, energize), neutral monsters and their buffs,
gold, and capture point advantage. See docs/cpu-eval-research.md for the reasoning.
"""

from __future__ import annotations

from src.types import GameState, Piece
from src.utils.monsters import MONSTER_INFO

MATE_SCORE = 100_000

SIDES = ("white", "black")

# --- Material -------------------------------------------------------------------
# Knights cannot jump and rooks start with a range of 3, so both are worth less
# than in standard chess. Rook value grows with its range (see moves/rook.py).
PAWN_VALUE = 100
KNIGHT_VALUE = 270
BISHOP_VALUE = 330
QUEEN_VALUE = 900
ROOK_BASE_VALUE = 400
ROOK_VALUE_PER_EXTRA_RANGE = 25
ROOK_BASE_RANGE = 3
ROOK_MAX_RANGE = 7

# --- Piece status ---------------------------------------------------------------
STUN_PENALTY_FRACTION = 0.15
# Index = bishop_debuff stacks. At 3 the opponent may simply remove the piece.
BISHOP_DEBUFF_PENALTY_FRACTION = (0.0, 0.05, 0.25, 0.8)
ENERGIZE_VALUE_PER_STACK = 0.5
FULL_ENERGIZE_BONUS = 30
CHECK_PROTECTION_VALUE = 80
CHECK_PENALTY = 30

# --- Neutral monsters -----------------------------------------------------------
# A piece that can no longer leave a monster's zone before its kill mark fires is
# as good as lost; one that still can only costs a tempo.
DOOMED_PIECE_PENALTY_FRACTION = 0.9
MONSTER_ZONE_TEMPO_PENALTY = 10
MONSTER_DAMAGE_VALUE_PER_HP = 12
SPAWN_SQUARE_WARNING_TURNS = 2
SPAWN_SQUARE_PENALTY_FRACTION = 0.8
KING_ON_SPAWN_SQUARE_PENALTY = 5_000
# Index = dragon stacks held by a side.
DRAGON_STACK_VALUE = (0, 40, 120, 180, 260, 400)
BOARD_HERALD_VALUE = 60
BARON_BASE_VALUE = 40
BARON_VALUE_PER_PAWN = 20

# --- Economy --------------------------------------------------------------------
# A pawn costs 2 gold; unspent gold is worth less than the piece it could buy.
GOLD_VALUE = 35
# Pawn buff thresholds match moves/pawn.py: >= 1 enables forward pawn captures,
# > 1 also makes pawns immune to enemy pawn captures.
CAPTURE_ADVANTAGE_FORWARD_CAPTURE_VALUE = 30
CAPTURE_ADVANTAGE_IMMUNITY_VALUE = 60

# --- Piece-square tables --------------------------------------------------------
# Indexed [rank][col] where rank 0 is the piece's own back rank.
_PAWN_TABLE = (
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, -5, -5, 0, 0, 0),
    (2, 4, 6, 10, 10, 6, 4, 2),
    (4, 8, 12, 18, 18, 12, 8, 4),
    (8, 12, 18, 26, 26, 18, 12, 8),
    (16, 22, 28, 36, 36, 28, 22, 16),
    (40, 45, 50, 55, 55, 50, 45, 40),
    (0, 0, 0, 0, 0, 0, 0, 0),
)
_KNIGHT_TABLE = (
    (-25, -20, -15, -15, -15, -15, -20, -25),
    (-20, -10, 0, 0, 0, 0, -10, -20),
    (-15, 0, 5, 8, 8, 5, 0, -15),
    (-15, 2, 8, 10, 10, 8, 2, -15),
    (-15, 0, 8, 10, 10, 8, 0, -15),
    (-15, 2, 5, 8, 8, 5, 2, -15),
    (-20, -10, 0, 2, 2, 0, -10, -20),
    (-25, -20, -15, -15, -15, -15, -20, -25),
)
_BISHOP_TABLE = (
    (-10, -5, -5, -5, -5, -5, -5, -10),
    (-5, 5, 0, 0, 0, 0, 5, -5),
    (-5, 5, 5, 5, 5, 5, 5, -5),
    (-5, 0, 5, 8, 8, 5, 0, -5),
    (-5, 2, 5, 8, 8, 5, 2, -5),
    (-5, 0, 2, 5, 5, 2, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-10, -5, -5, -5, -5, -5, -5, -10),
)
_ROOK_TABLE = (
    (0, 0, 2, 5, 5, 2, 0, 0),
    (0, 0, 0, 2, 2, 0, 0, 0),
    (-2, 0, 0, 2, 2, 0, 0, -2),
    (-2, 0, 0, 2, 2, 0, 0, -2),
    (-2, 0, 0, 2, 2, 0, 0, -2),
    (0, 2, 2, 4, 4, 2, 2, 0),
    (5, 8, 8, 8, 8, 8, 8, 5),
    (0, 0, 0, 2, 2, 0, 0, 0),
)
_QUEEN_TABLE = (
    (-10, -5, -5, -2, -2, -5, -5, -10),
    (-5, 0, 2, 0, 0, 0, 0, -5),
    (-5, 2, 3, 3, 3, 3, 0, -5),
    (-2, 0, 3, 3, 3, 3, 0, -2),
    (-2, 0, 3, 3, 3, 3, 0, -2),
    (-5, 0, 3, 3, 3, 3, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-10, -5, -5, -2, -2, -5, -5, -10),
)
_KING_TABLE = (
    (10, 15, 5, 0, 0, 5, 15, 10),
    (5, 5, -5, -10, -10, -5, 5, 5),
    (-15, -20, -20, -25, -25, -20, -20, -15),
    (-25, -30, -30, -35, -35, -30, -30, -25),
    (-30, -35, -35, -40, -40, -35, -35, -30),
    (-30, -35, -35, -40, -40, -35, -35, -30),
    (-30, -35, -35, -40, -40, -35, -35, -30),
    (-30, -35, -35, -40, -40, -35, -35, -30),
)
_TABLES = {
    "pawn": _PAWN_TABLE,
    "knight": _KNIGHT_TABLE,
    "bishop": _BISHOP_TABLE,
    "rook": _ROOK_TABLE,
    "queen": _QUEEN_TABLE,
    "king": _KING_TABLE,
}


def get_rook_range(turn_count: int) -> int:
    """Rook range for a given turn, mirroring moves/rook.py (capped at the board size)."""
    rook_range = ROOK_BASE_RANGE
    if turn_count >= 15:
        rook_range += (turn_count - 10) // 5
    return min(rook_range, ROOK_MAX_RANGE)


def get_material_value(piece_type: str, turn_count: int = 0) -> int:
    """Centipawn value of a piece type under this variant's rules (kings and monsters are 0)."""
    if "neutral" in piece_type:
        return 0
    if "pawn" in piece_type:
        return PAWN_VALUE
    if "knight" in piece_type:
        return KNIGHT_VALUE
    if "bishop" in piece_type:
        return BISHOP_VALUE
    if "rook" in piece_type:
        return ROOK_BASE_VALUE + ROOK_VALUE_PER_EXTRA_RANGE * (get_rook_range(turn_count) - ROOK_BASE_RANGE)
    if "queen" in piece_type:
        return QUEEN_VALUE
    return 0


def get_square_bonus(piece_type: str, row: int, col: int) -> int:
    """Piece-square bonus for a piece type on a board square."""
    side, _, name = piece_type.partition("_")
    table = _TABLES.get(name)
    if table is None:
        return 0
    rank = row if side == "black" else 7 - row
    return table[rank][col]


def _in_zone(row: int, col: int, center: list) -> bool:
    return abs(row - center[0]) <= 1 and abs(col - center[1]) <= 1


def _get_live_monsters(board_state: list) -> list[dict]:
    """Return the monsters currently on the board with their position and health."""
    live = []
    seen = set()
    for monster_type, info in MONSTER_INFO.items():
        row, col = info["position"]
        for piece in board_state[row][col] or []:
            if piece.get("type") == monster_type and monster_type not in seen:
                seen.add(monster_type)
                live.append({
                    "type": monster_type,
                    "position": info["position"],
                    "health": piece.get("health", info["max_health"]),
                    "max_health": info["max_health"],
                })
    return live


def _get_spawn_squares_due_soon(turn_count: int) -> list[list]:
    """Squares where a monster will spawn within the warning window."""
    squares = []
    for upcoming in range(turn_count + 1, turn_count + SPAWN_SQUARE_WARNING_TURNS + 1):
        if upcoming % 10 == 0:
            squares.append(MONSTER_INFO["neutral_dragon"]["position"])
        if upcoming in (10, 20):
            squares.append(MONSTER_INFO["neutral_board_herald"]["position"])
        if upcoming > 20 and (upcoming - 20) % 15 == 0:
            squares.append(MONSTER_INFO["neutral_baron_nashor"]["position"])
    return squares


def _can_escape_kill_mark(piece: Piece, side: str, turn_count: int) -> bool:
    """Whether the piece's owner still gets a move before its monster kill mark fires.

    The mark fires on the update that brings turn_count to the marked value while the
    piece is still in the zone, so the owner needs a move that completes on or before
    that turn.
    """
    kill_mark = piece.get("neutral_kill_mark", -1)
    if kill_mark < turn_count:
        # No pending mark: one will be placed two turns out on the next update.
        return True
    side_to_move = "white" if turn_count % 2 == 0 else "black"
    next_owner_turn = turn_count if side_to_move == side else turn_count + 1
    return next_owner_turn + 1 <= kill_mark


def _score_piece(piece: Piece, side: str, row: int, col: int, turn_count: int,
                 live_monsters: list[dict], spawn_squares: list[list]) -> float:
    piece_type = piece["type"]
    value = get_material_value(piece_type, turn_count)
    score = value + get_square_bonus(piece_type, row, col)

    if "king" in piece_type:
        score += CHECK_PROTECTION_VALUE * (piece.get("check_protection") or 0)
        if [row, col] in spawn_squares:
            score -= KING_ON_SPAWN_SQUARE_PENALTY
        return score

    if piece.get("is_stunned"):
        score -= value * STUN_PENALTY_FRACTION

    debuff = min(piece.get("bishop_debuff", 0) or 0, 3)
    score -= value * BISHOP_DEBUFF_PENALTY_FRACTION[debuff]

    stacks = piece.get("energize_stacks", 0) or 0
    if "bishop" in piece_type and stacks:
        score += stacks * ENERGIZE_VALUE_PER_STACK
        if stacks >= 100:
            score += FULL_ENERGIZE_BONUS

    for monster in live_monsters:
        if _in_zone(row, col, monster["position"]):
            if _can_escape_kill_mark(piece, side, turn_count):
                score -= MONSTER_ZONE_TEMPO_PENALTY
            else:
                score -= value * DOOMED_PIECE_PENALTY_FRACTION
            break

    if [row, col] in spawn_squares:
        score -= value * SPAWN_SQUARE_PENALTY_FRACTION

    return score


def _score_side_globals(game_state: GameState, side: str, pawn_count: int) -> float:
    score = GOLD_VALUE * game_state.get("gold_count", {}).get(side, 0)

    buffs = (game_state.get("neutral_buff_log") or {}).get(side) or {}
    stacks = min((buffs.get("dragon") or {}).get("stacks", 0), 5)
    score += DRAGON_STACK_VALUE[stacks]
    if (buffs.get("board_herald") or {}).get("active"):
        score += BOARD_HERALD_VALUE
    if (buffs.get("baron_nashor") or {}).get("active"):
        score += BARON_BASE_VALUE + BARON_VALUE_PER_PAWN * pawn_count

    advantage = game_state.get("capture_point_advantage")
    if advantage and advantage[0] == side and pawn_count:
        if advantage[1] > 1:
            score += CAPTURE_ADVANTAGE_IMMUNITY_VALUE
        elif advantage[1] >= 1:
            score += CAPTURE_ADVANTAGE_FORWARD_CAPTURE_VALUE

    if (game_state.get("check") or {}).get(side):
        score -= CHECK_PENALTY

    return score


def evaluate(game_state: GameState, side: str = "black") -> int:
    """Score a game state in centipawns from `side`'s point of view.

    Positive means `side` is better. A decided game returns +/- MATE_SCORE and a draw 0.
    """
    opponent = "white" if side == "black" else "black"
    side_lost = game_state.get(f"{side}_defeat", False)
    opponent_lost = game_state.get(f"{opponent}_defeat", False)
    if side_lost and opponent_lost:
        return 0
    if side_lost:
        return -MATE_SCORE
    if opponent_lost:
        return MATE_SCORE

    board_state = game_state["board_state"]
    turn_count = game_state["turn_count"]
    live_monsters = _get_live_monsters(board_state)
    spawn_squares = _get_spawn_squares_due_soon(turn_count)

    totals = {"white": 0.0, "black": 0.0}
    pawn_counts = {"white": 0, "black": 0}
    non_king_counts = {"white": 0, "black": 0}
    lowest_marked_value = {"white": None, "black": None}
    pieces_in_zone = {monster["type"]: {"white": 0, "black": 0} for monster in live_monsters}

    for row in range(8):
        for col in range(8):
            for piece in board_state[row][col] or []:
                piece_type = piece.get("type", "")
                piece_side = piece_type.partition("_")[0]
                if piece_side not in totals:
                    continue
                totals[piece_side] += _score_piece(
                    piece, piece_side, row, col, turn_count, live_monsters, spawn_squares
                )
                if "king" in piece_type:
                    continue
                non_king_counts[piece_side] += 1
                if "pawn" in piece_type:
                    pawn_counts[piece_side] += 1
                if piece.get("marked_for_death"):
                    value = get_material_value(piece_type, turn_count)
                    current = lowest_marked_value[piece_side]
                    lowest_marked_value[piece_side] = value if current is None else min(current, value)
                for monster in live_monsters:
                    if _in_zone(row, col, monster["position"]):
                        pieces_in_zone[monster["type"]][piece_side] += 1

    # Only the two kings left is a draw.
    if non_king_counts["white"] == 0 and non_king_counts["black"] == 0:
        return 0

    for current_side in SIDES:
        totals[current_side] += _score_side_globals(game_state, current_side, pawn_counts[current_side])
        # A side with marked pieces must surrender exactly one of them.
        if lowest_marked_value[current_side] is not None:
            totals[current_side] -= lowest_marked_value[current_side]

    # Credit damage already dealt to a monster to the side better placed to finish it.
    for monster in live_monsters:
        missing_health = monster["max_health"] - monster["health"]
        if missing_health <= 0:
            continue
        in_zone = pieces_in_zone[monster["type"]]
        if in_zone["white"] == in_zone["black"]:
            continue
        leader = "white" if in_zone["white"] > in_zone["black"] else "black"
        totals[leader] += MONSTER_DAMAGE_VALUE_PER_HP * missing_health

    return int(round(totals[side] - totals[opponent]))
