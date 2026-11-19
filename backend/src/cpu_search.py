"""Lookahead search for the CPU player.

Iterative-deepening alpha-beta over states produced by the real game update pipeline
(simulate_game_update), so every variant rule is applied exactly as in a live game.
The side to act is read from each state's turn count rather than assumed to alternate,
because queen resets, surrenders, bishop debuff resolutions, promotions and stun
skips all give one side consecutive actions.
"""

from __future__ import annotations

import copy
import random
import time
from typing import Optional

import src.cpu_player as cpu_player
import src.utils as utils
from src.cpu_eval import MATE_SCORE, evaluate, get_material_value, get_square_bonus
from src.log import logger, suppress_logging
from src.types import GameState
from src.utils.game_update_pipeline import simulate_game_update

DEFAULT_TIME_LIMIT_SECONDS = 5.0
MAX_SEARCH_DEPTH = 4
QUIESCENCE_DEPTH = 2
MAX_FORCED_STEPS = 4
PURCHASE_SQUARES_PER_PIECE = 2
# Root moves within this many centipawns of the best search score are treated as equal;
# among those, moves within STATIC_TIE_MARGIN of the best immediate score are picked at random.
TIE_BREAK_MARGIN = 8
STATIC_TIE_MARGIN = 2
REVERSAL_PENALTY = 25
PROMOTION_PIECE = "queen"

BOARD_MOVE_TYPES = ("move", "capture", "castle")


class SearchTimeout(Exception):
    """Raised inside the search when the time budget runs out."""


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def get_side_to_move(game_state: GameState) -> str:
    return "white" if game_state["turn_count"] % 2 == 0 else "black"


def _copy_state(game_state: GameState) -> GameState:
    """Deep copy a state while sharing its (read-only) previous_state by reference."""
    previous_state = game_state.pop("previous_state", None)
    try:
        state_copy = copy.deepcopy(game_state)
    finally:
        if previous_state is not None:
            game_state["previous_state"] = previous_state
    if previous_state is not None:
        state_copy["previous_state"] = previous_state
    return state_copy


def _is_game_over(game_state: GameState) -> bool:
    return bool(game_state.get("black_defeat") or game_state.get("white_defeat"))


def _find_pieces(game_state: GameState, predicate) -> list[tuple[list, dict]]:
    found = []
    for row in range(8):
        for col in range(8):
            for piece in game_state["board_state"][row][col] or []:
                if predicate(piece):
                    found.append(([row, col], piece))
    return found


# ---------------------------------------------------------------------------
# Forced steps (promotion, surrender, bishop debuff resolution)
# ---------------------------------------------------------------------------

def get_forced_action(game_state: GameState, side: str) -> Optional[dict]:
    """Return the single action `side` must take before a normal move, if any."""
    opposing_side = "white" if side == "black" else "black"
    turn_count = game_state["turn_count"]

    promotion_row = 7 if side == "black" else 0
    for col in range(8):
        for piece in game_state["board_state"][promotion_row][col] or []:
            if piece.get("type") == f"{side}_pawn":
                return {"type": "promote", "from_pos": [promotion_row, col], "piece_type": f"{side}_{PROMOTION_PIECE}"}

    marked = _find_pieces(
        game_state,
        lambda piece: side in piece.get("type", "") and piece.get("marked_for_death", False),
    )
    if marked and any(not piece.get("is_stunned", False) for _, piece in marked):
        position, piece = min(marked, key=lambda entry: get_material_value(entry[1]["type"], turn_count))
        return {"type": "sacrifice", "from_pos": position, "piece_type": piece["type"]}

    debuffed = _find_pieces(
        game_state,
        lambda piece: opposing_side in piece.get("type", "") and piece.get("bishop_debuff", 0) == 3,
    )
    if debuffed:
        position, piece = max(debuffed, key=lambda entry: get_material_value(entry[1]["type"], turn_count))
        return {"type": "bishop_capture", "from_pos": position, "piece_type": piece["type"]}

    return None


# ---------------------------------------------------------------------------
# Applying actions
# ---------------------------------------------------------------------------

def mutate_for_action(old_state: GameState, new_state: GameState, action: dict, side: str) -> None:
    """Edit new_state the way a client would to submit `action`."""
    action_type = action["type"]
    board = new_state["board_state"]

    if action_type in BOARD_MOVE_TYPES:
        old_state["position_in_play"] = action["from_pos"]
        new_state["position_in_play"] = action["from_pos"]
        captured = cpu_player._apply_move_to_board(board, action, old_state["board_state"], side)
        if captured and "neutral" not in captured:
            new_state["captured_pieces"][side].append(captured)
        return

    if action_type == "purchase":
        board[action["to_pos"][0]][action["to_pos"][1]] = [cpu_player.build_purchased_piece(action["piece_type"])]
        return

    row, col = action["from_pos"]
    square = board[row][col] or []
    piece_type = action["piece_type"]

    if action_type == "promote":
        others = [piece for piece in square if piece.get("type") != f"{side}_pawn"]
        board[row][col] = others + [cpu_player.build_purchased_piece(piece_type)]
    elif action_type == "sacrifice":
        board[row][col] = cpu_player.remove_first_matching(
            square, lambda piece: piece.get("type") == piece_type and piece.get("marked_for_death", False)
        )
    elif action_type == "bishop_capture":
        board[row][col] = cpu_player.remove_first_matching(
            square, lambda piece: piece.get("type") == piece_type and piece.get("bishop_debuff", 0) == 3
        )
        new_state["captured_pieces"][side].append(piece_type)
        new_state["bishop_special_captures"] = [{"position": [row, col], "type": piece_type}]
    elif action_type == "bishop_spare":
        for piece in square:
            if piece.get("type") == piece_type and piece.get("bishop_debuff", 0) == 3:
                piece["bishop_debuff"] = 0
                break


def apply_action(game_state: GameState, action: dict, side: str) -> Optional[GameState]:
    """Return the state after `side` takes one action, or None if the pipeline rejects it.

    The input state is not modified. Besides running the pipeline, this records the
    move and sword pickup as finalize_game_state would, because later steps (bishop
    debuff captures) read latest_movement.
    """
    old_state = _copy_state(game_state)
    new_state = _copy_state(game_state)
    mutate_for_action(old_state, new_state, action, side)

    try:
        moved_pieces = utils.determine_pieces_that_have_moved(new_state["board_state"], old_state["board_state"])
    except Exception:
        return None

    try:
        result = simulate_game_update(old_state, new_state)
    except Exception:
        # A pipeline crash on a speculative state must not cost the CPU its turn;
        # treat the action as unavailable.
        return None
    if result is None:
        return None
    if action["type"] in BOARD_MOVE_TYPES and result["check"][side]:
        return None

    utils.record_moved_pieces_this_turn(result, moved_pieces)
    utils.exhaust_sword_in_the_stone(result, moved_pieces)
    old_state.pop("previous_state", None)
    result["previous_state"] = old_state
    return result


def resolve_forced_steps(game_state: GameState) -> GameState:
    """Play out pending forced steps for whichever side owes them."""
    for _ in range(MAX_FORCED_STEPS):
        if _is_game_over(game_state):
            break
        side = get_side_to_move(game_state)
        forced = get_forced_action(game_state, side)
        if forced is None:
            break
        next_state = apply_action(game_state, forced, side)
        if next_state is None and forced["type"] == "bishop_capture":
            next_state = apply_action(game_state, {**forced, "type": "bishop_spare"}, side)
        if next_state is None:
            break
        game_state = next_state
    return game_state


def play_action(game_state: GameState, action: dict, side: str) -> Optional[GameState]:
    """Apply an action and any forced steps that follow it."""
    result = apply_action(game_state, action, side)
    if result is None:
        return None
    return resolve_forced_steps(result)


# ---------------------------------------------------------------------------
# Move generation and ordering
# ---------------------------------------------------------------------------

def _get_piece_type_at(game_state: GameState, position: list, side_or_kind: str) -> Optional[str]:
    for piece in game_state["board_state"][position[0]][position[1]] or []:
        if side_or_kind in piece.get("type", ""):
            return piece["type"]
    return None


def _get_victim_value(game_state: GameState, action: dict, side: str) -> int:
    opposing_side = "white" if side == "black" else "black"
    victim = _get_piece_type_at(game_state, action["capture_at"], opposing_side)
    if victim is None:
        # A monster kill: worth a buff and gold rather than material.
        return get_material_value(f"{side}_knight")
    return get_material_value(victim, game_state["turn_count"])


def _order_key(game_state: GameState, action: dict, side: str) -> float:
    """Sort key so captures are searched first, most valuable victim by cheapest attacker."""
    if action["type"] != "capture":
        return 0
    attacker = _get_piece_type_at(game_state, action["from_pos"], side) or ""
    attacker_value = get_material_value(attacker, game_state["turn_count"])
    return -(10_000 + _get_victim_value(game_state, action, side) * 10 - attacker_value)


def get_board_actions(game_state: GameState, side: str, captures_only: bool = False) -> list[dict]:
    """Candidate board moves for `side`, ordered for search (legality is checked on apply)."""
    actions = cpu_player._get_raw_moves(game_state, side)
    if captures_only:
        actions = [action for action in actions if action["type"] == "capture"]
    actions.sort(key=lambda action: _order_key(game_state, action, side))
    return actions


def get_purchase_actions(game_state: GameState, side: str) -> list[dict]:
    """The most promising squares for each affordable piece."""
    by_piece = {}
    for purchase in cpu_player._get_purchase_moves(game_state, side):
        by_piece.setdefault(purchase["piece_type"], []).append(purchase)

    shortlisted = []
    for piece_type, purchases in by_piece.items():
        purchases.sort(key=lambda p: -get_square_bonus(piece_type, p["to_pos"][0], p["to_pos"][1]))
        shortlisted.extend(purchases[:PURCHASE_SQUARES_PER_PIECE])
    return shortlisted


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class _Searcher:
    def __init__(self, side: str, deadline: float):
        self.side = side
        self.deadline = deadline
        self.nodes = 0

    def _check_time(self) -> None:
        self.nodes += 1
        if time.monotonic() > self.deadline:
            raise SearchTimeout()

    def _static_score(self, game_state: GameState, ply: int) -> int:
        score = evaluate(game_state, self.side)
        # Prefer the quickest win and the slowest loss.
        if score >= MATE_SCORE:
            return score - ply
        if score <= -MATE_SCORE:
            return score + ply
        return score

    def search(self, game_state: GameState, depth: int, alpha: float, beta: float, ply: int) -> float:
        self._check_time()
        if _is_game_over(game_state):
            return self._static_score(game_state, ply)
        if depth <= 0:
            return self.quiescence(game_state, alpha, beta, QUIESCENCE_DEPTH, ply)

        mover = get_side_to_move(game_state)
        maximizing = mover == self.side
        best = -float("inf") if maximizing else float("inf")
        has_legal_action = False

        for action in get_board_actions(game_state, mover):
            child = play_action(game_state, action, mover)
            if child is None:
                continue
            has_legal_action = True
            score = self.search(child, depth - 1, alpha, beta, ply + 1)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if alpha >= beta:
                break

        if not has_legal_action:
            return self._no_moves_score(game_state, mover, ply)
        return best

    def quiescence(self, game_state: GameState, alpha: float, beta: float, depth: int, ply: int) -> float:
        """Extend the search through captures so a leaf is not judged mid-exchange."""
        self._check_time()
        stand_pat = self._static_score(game_state, ply)
        if depth <= 0 or _is_game_over(game_state):
            return stand_pat

        mover = get_side_to_move(game_state)
        maximizing = mover == self.side
        best = stand_pat
        if maximizing:
            alpha = max(alpha, best)
        else:
            beta = min(beta, best)
        if alpha >= beta:
            return best

        for action in get_board_actions(game_state, mover, captures_only=True):
            child = play_action(game_state, action, mover)
            if child is None:
                continue
            score = self.quiescence(child, alpha, beta, depth - 1, ply + 1)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if alpha >= beta:
                break
        return best

    def _no_moves_score(self, game_state: GameState, mover: str, ply: int) -> float:
        """Checkmate if the stuck side is in check, otherwise a draw."""
        if not game_state["check"].get(mover):
            return 0
        mated_score = -MATE_SCORE + ply if mover == self.side else MATE_SCORE - ply
        return mated_score


def _is_reversal(action: dict, last_own_move: Optional[dict]) -> bool:
    return bool(
        last_own_move
        and action["type"] == "move"
        and action["from_pos"] == last_own_move.get("to")
        and action["to_pos"] == last_own_move.get("from")
    )


def _search_root(game_state: GameState, side: str, searcher: _Searcher, max_depth: int,
                 last_own_move: Optional[dict]) -> tuple[list[dict], float]:
    """Score every legal root action by iterative deepening until the time runs out."""
    candidates = []
    for action in get_board_actions(game_state, side) + get_purchase_actions(game_state, side):
        child = play_action(game_state, action, side)
        if child is None:
            continue
        penalty = REVERSAL_PENALTY if _is_reversal(action, last_own_move) else 0
        static_score = evaluate(child, side) - penalty
        candidates.append({"action": action, "child": child, "penalty": penalty,
                           "static_score": static_score, "score": static_score})

    if not candidates:
        return [], 0

    completed_depth = 0
    for depth in range(1, max_depth + 1):
        candidates.sort(key=lambda candidate: -candidate["score"])
        scores = []
        alpha = -float("inf")
        try:
            for candidate in candidates:
                # Search with a slightly widened window so near-ties keep exact scores.
                score = searcher.search(candidate["child"], depth - 1, alpha - TIE_BREAK_MARGIN - 1, float("inf"), 1)
                score -= candidate["penalty"]
                scores.append(score)
                alpha = max(alpha, score)
        except SearchTimeout:
            # The first move searched is the previous best, so any finished move that
            # beats it at this depth is a real improvement. Unfinished moves are
            # dropped below the finished ones rather than compared across depths.
            if scores:
                for candidate, score in zip(candidates, scores):
                    candidate["score"] = score
                for candidate in candidates[len(scores):]:
                    candidate["score"] = -float("inf")
                completed_depth = depth - 0.5
            break
        for candidate, score in zip(candidates, scores):
            candidate["score"] = score
        completed_depth = depth
        if max(scores) >= MATE_SCORE - max_depth - QUIESCENCE_DEPTH - 1:
            break

    return candidates, completed_depth


def _pick_best(candidates: list[dict]) -> dict:
    """Pick among the top-scoring candidates.

    Moves the search rates as near-equal usually reach the same gain at different
    times (take the dragon now or next turn), so prefer the one that is better
    immediately, then choose at random among any that are still level.
    """
    best_score = max(candidate["score"] for candidate in candidates)
    near_best = [c for c in candidates if c["score"] >= best_score - TIE_BREAK_MARGIN]
    best_static = max(candidate["static_score"] for candidate in near_best)
    return random.choice([c for c in near_best if c["static_score"] >= best_static - STATIC_TIE_MARGIN])


def choose_action(
    game_state: GameState,
    side: str = cpu_player.CPU_SIDE,
    time_limit: float = DEFAULT_TIME_LIMIT_SECONDS,
    max_depth: int = MAX_SEARCH_DEPTH,
    last_own_move: Optional[dict] = None,
) -> Optional[dict]:
    """Pick the best board move or purchase for `side`, or None if it has no legal action.

    `last_own_move` ({"from": [r, c], "to": [r, c]}) lets the search discourage
    shuffling a piece straight back, since the game has no repetition rule.
    """
    started = time.monotonic()
    searcher = _Searcher(side, started + time_limit)
    with suppress_logging():
        candidates, completed_depth = _search_root(game_state, side, searcher, max_depth, last_own_move)

    if not candidates:
        return None

    chosen = _pick_best(candidates)
    logger.info(
        f"CPU search: depth {completed_depth}, {searcher.nodes} nodes, "
        f"{time.monotonic() - started:.2f}s, score {chosen['score']}, {len(candidates)} legal actions"
    )
    return chosen["action"]
