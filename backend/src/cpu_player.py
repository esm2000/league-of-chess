"""CPU player system: background polling, move generation, and move application."""

from __future__ import annotations

import copy
import datetime
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from bson.objectid import ObjectId
from fastapi import Response

import src.moves as moves
from src.database import mongo_client
from src.log import logger
from src.types import GameState, MoveResult
from src.utils.board_analysis import get_piece_value
from src.utils.check_checkmate import trim_king_moves


CPU_POLL_INTERVAL_SECONDS = 1.5
CPU_LEASE_TIMEOUT_SECONDS = 30
CPU_SIDE = "black"
OPPONENT_SIDE = "white"
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"
MEDIUM_ALGORITHM_PROBABILITY = 0.5
HARD_THINK_SECONDS = 5
PROMOTION_PIECES = ["queen", "rook", "bishop", "knight"]
ALGORITHM_PROMOTION_PIECE = "queen"
CPU_MOVE_DELAY_SECONDS = 0.75
PURCHASABLE_PIECES = {"pawn": 2, "knight": 6, "bishop": 6, "rook": 10}
MAX_CLAIMS_PER_POLL = 8
MAX_CPU_WORKERS = 4
CPU_GAME_TIMEOUT_SECONDS = 45
PURCHASE_PROBABILITY = 0.2


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------

def _place_piece_on_square(board, from_pos, to_pos):
    """Move piece from one square to another, preserving neutral monsters on the target.

    Non-neutral occupants on the target square are replaced; neutrals are kept and
    stacked with the arriving piece.  This handles empty squares, pure-monster squares,
    and mixed (enemy + monster) squares correctly.
    """
    from_r, from_c = from_pos
    to_r, to_c = to_pos
    target = board[to_r][to_c] or []
    moving = board[from_r][from_c] or []
    neutrals = [p for p in target if "neutral" in p.get("type", "")]
    board[to_r][to_c] = neutrals + moving if neutrals else moving
    board[from_r][from_c] = None


def build_purchased_piece(piece_type: str) -> dict:
    """Build a fresh piece dict of the given type with its starting attributes."""
    new_piece = {"type": piece_type}
    if "bishop" in piece_type:
        new_piece["energize_stacks"] = 0
    if "pawn" in piece_type:
        new_piece["pawn_buff"] = 0
    return new_piece


def remove_first_matching(square, predicate):
    """Return the square's pieces without the first one matching predicate (None if empty)."""
    remaining = list(square or [])
    for index, piece in enumerate(remaining):
        if predicate(piece):
            remaining.pop(index)
            break
    return remaining or None


def _get_opposing_side(side: str) -> str:
    return "white" if side == "black" else "black"


def _apply_move_to_board(board, move, ref_board=None, side: str = CPU_SIDE):
    """Apply a move (castle, capture, or normal) by `side` to the board.

    Uses ref_board (the board before this move) to identify the captured piece.
    Returns the captured piece type string, or None.
    """
    opposing_side = _get_opposing_side(side)
    from_r, from_c = move["from_pos"]
    to_r, to_c = move["to_pos"]

    if move["type"] == "castle":
        _place_piece_on_square(board, [from_r, from_c], [to_r, to_c])
        rook_from, rook_to = _get_castle_rook_positions(to_c)
        _place_piece_on_square(board, [to_r, rook_from], [to_r, rook_to])
        return None

    captured_piece_type = None
    if move["type"] == "capture":
        cap_r, cap_c = move["capture_at"]
        source = ref_board or board
        for piece in source[cap_r][cap_c] or []:
            if opposing_side in piece.get("type", "") or "neutral" in piece.get("type", ""):
                captured_piece_type = piece["type"]
                break

    _place_piece_on_square(board, [from_r, from_c], [to_r, to_c])

    if move["type"] == "capture":
        cap_r, cap_c = move["capture_at"]
        if [cap_r, cap_c] != [to_r, to_c]:
            # Remove only the captured piece, preserve neutrals on the same square
            square = board[cap_r][cap_c] or []
            board[cap_r][cap_c] = [p for p in square if p.get("type") != captured_piece_type] or None

    return captured_piece_type


# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------

def get_all_valid_moves(game_state: GameState) -> list[dict]:
    """Generate every valid move for black, filtering moves that leave the king in check."""
    raw_moves = _get_raw_moves(game_state)
    valid_moves = []

    for move in raw_moves:
        if _move_leaves_king_safe(game_state, move):
            valid_moves.append(move)

    return valid_moves


def _get_raw_moves(game_state: GameState, side: str = CPU_SIDE) -> list[dict]:
    """Get all candidate moves for `side`'s pieces without king-safety filtering."""
    raw_moves = []
    prev_state = game_state.get("previous_state")

    for row in range(8):
        for col in range(8):
            square = game_state["board_state"][row][col] or []
            for piece in square:
                if side not in piece.get("type", ""):
                    continue
                if piece.get("is_stunned", False):
                    continue

                moves_info = moves.get_moves(prev_state, game_state, [row, col], piece)

                if "king" in piece["type"]:
                    moves_info = trim_king_moves(moves_info, prev_state, game_state, side)

                # Build a lookup for captures: to_pos -> capture_at. A destination can offer
                # two captures (the piece standing on it and an adjacent enemy bishop);
                # landing on an occupied square must capture the piece that is there.
                capture_lookup = {}
                for cap in moves_info["possible_captures"]:
                    key = (cap[0][0], cap[0][1])
                    if key not in capture_lookup or cap[1] == cap[0]:
                        capture_lookup[key] = cap[1]

                # Collect moves from possible_moves
                for to_pos in moves_info["possible_moves"]:
                    to_key = (to_pos[0], to_pos[1])
                    if to_key in capture_lookup:
                        raw_moves.append({
                            "type": "capture",
                            "from_pos": [row, col],
                            "to_pos": to_pos,
                            "capture_at": capture_lookup[to_key],
                        })
                    else:
                        raw_moves.append({
                            "type": "move",
                            "from_pos": [row, col],
                            "to_pos": to_pos,
                        })

                # Collect castle moves for king
                if "king" in piece["type"]:
                    for castle_pos in moves_info.get("castle_moves", []):
                        raw_moves.append({
                            "type": "castle",
                            "from_pos": [row, col],
                            "to_pos": castle_pos,
                        })

    return raw_moves


def simulate_move(game_state: GameState, move: dict, side: str = CPU_SIDE) -> Optional[GameState]:
    """Return the state after `side` plays a board move, or None if the move is illegal.

    Runs the full game update pipeline (without DB) so that side effects like
    adjacent captures, bishop debuffs, neutral monster spawns/attacks, and queen
    stun are all reflected. A move that leaves the mover's king in check is illegal.
    The input state is not modified.
    """
    from src.utils.game_update_pipeline import simulate_game_update

    # Pretend the select step already happened so the pipeline treats this as a move step
    old_state = copy.deepcopy(game_state)
    old_state["position_in_play"] = move["from_pos"]

    new_state = copy.deepcopy(old_state)
    captured = _apply_move_to_board(new_state["board_state"], move, old_state["board_state"], side)
    if captured and "neutral" not in captured:
        new_state["captured_pieces"][side].append(captured)

    result = simulate_game_update(old_state, new_state)
    if result is None or result["check"][side]:
        return None
    return result


def _move_leaves_king_safe(game_state: GameState, move: dict) -> bool:
    """Return True if applying this move does NOT leave the black king in check."""
    return simulate_move(game_state, move) is not None


def _get_castle_rook_positions(king_target_col: int) -> tuple[int, int]:
    """Return (rook_from_col, rook_to_col) for a castle move."""
    if king_target_col == 2:  # queenside
        return 0, 3
    else:  # kingside (col 6)
        return 7, 5


def get_marked_for_death_moves(game_state: GameState) -> list[dict]:
    """Get sacrifice options when black pieces are marked for death."""
    sacrifice_moves = []
    for row in range(8):
        for col in range(8):
            for piece in game_state["board_state"][row][col] or []:
                if CPU_SIDE in piece.get("type", "") and piece.get("marked_for_death", False):
                    sacrifice_moves.append({
                        "type": "sacrifice",
                        "from_pos": [row, col],
                        "piece_type": piece["type"],
                    })
    return sacrifice_moves


def _has_marked_for_death(game_state: GameState) -> bool:
    """Check if any non-stunned black pieces are marked for death."""
    return any(
        CPU_SIDE in piece.get("type", "") and piece.get("marked_for_death", False) and not piece.get("is_stunned", False)
        for row in game_state["board_state"]
        for square in row
        for piece in square or []
    )


def _is_monster_adjacent(row, col, game_state):
    """Return True if the square is adjacent to or on a live neutral monster."""
    from src.utils.monsters import MONSTER_INFO, is_neutral_monster_spawned
    for monster_type, info in MONSTER_INFO.items():
        if not is_neutral_monster_spawned(monster_type, game_state["board_state"]):
            continue
        mr, mc = info["position"]
        if abs(row - mr) <= 1 and abs(col - mc) <= 1:
            return True
    return False


def _get_purchase_moves(game_state: GameState, side: str = CPU_SIDE) -> list[dict]:
    """Generate purchase options for affordable pieces on valid empty squares in `side`'s half."""
    gold = game_state["gold_count"].get(side, 0)
    if gold < 2:
        return []

    sword_pos = game_state.get("sword_in_the_stone_position")
    purchases = []
    for piece_name, cost in PURCHASABLE_PIECES.items():
        if cost > gold:
            continue
        piece_type = f"{side}_{piece_name}"
        for row in (range(4) if side == "black" else range(4, 8)):
            for col in range(8):
                if game_state["board_state"][row][col] is not None:
                    continue
                if sword_pos and [row, col] == sword_pos:
                    continue
                if _is_monster_adjacent(row, col, game_state):
                    continue
                purchases.append({
                    "type": "purchase",
                    "piece_type": piece_type,
                    "to_pos": [row, col],
                    "cost": cost,
                })
    return purchases


def get_bishop_debuff_targets(game_state: GameState) -> list[dict]:
    """White pieces with full bishop debuff stacks that black must capture or spare."""
    targets = []
    for row in range(8):
        for col in range(8):
            for piece in game_state["board_state"][row][col] or []:
                if OPPONENT_SIDE in piece.get("type", "") and piece.get("bishop_debuff", 0) == 3:
                    targets.append({"from_pos": [row, col], "piece_type": piece["type"]})
    return targets


def _is_pawn_promotion_needed(game_state: GameState) -> bool:
    """Check if a black pawn is on row 7 (promotion rank for black)."""
    for col in range(8):
        for piece in game_state["board_state"][7][col] or []:
            if piece.get("type") == "black_pawn":
                return True
    return False


# ---------------------------------------------------------------------------
# Move application
# ---------------------------------------------------------------------------

def apply_cpu_move(game_id: str, game_state: GameState, move: dict, promotion_piece: Optional[str] = None) -> dict:
    """Apply a CPU move via the existing game update pipeline (select + move).

    promotion_piece names the piece a promoting pawn becomes; random if not given.
    """
    import src.api as api

    if move["type"] == "sacrifice":
        return _apply_sacrifice(game_id, game_state, move)

    if move["type"] == "purchase":
        return _apply_purchase(game_id, game_state, move)

    # Step 1: Select the piece (set position_in_play)
    select_state = copy.deepcopy(game_state)
    select_state["position_in_play"] = move["from_pos"]
    select_request = api.GameStateRequest(**select_state)
    game_after_select = api.update_game_state(game_id, select_request, Response(), player=False)

    # Pause so the frontend can show which piece the CPU selected
    time.sleep(CPU_MOVE_DELAY_SECONDS)

    # Step 2: Move the piece on the board
    move_state = copy.deepcopy(game_after_select)
    captured = _apply_move_to_board(move_state["board_state"], move, game_after_select["board_state"])
    # Record capture (neutral monster captures handled by pipeline)
    if captured and "neutral" not in captured:
        move_state["captured_pieces"][CPU_SIDE].append(captured)

    move_request = api.GameStateRequest(**move_state)
    game_after_move = api.update_game_state(game_id, move_request, Response(), player=False)

    # Step 3: Handle pawn promotion if needed
    if _is_pawn_promotion_needed(game_after_move):
        game_after_move = _apply_pawn_promotion(game_id, game_after_move, promotion_piece)

    return game_after_move


def _apply_sacrifice(game_id: str, game_state: GameState, move: dict) -> dict:
    """Remove one marked-for-death black piece from the board."""
    import src.api as api

    sacrifice_state = copy.deepcopy(game_state)
    row, col = move["from_pos"]
    square = sacrifice_state["board_state"][row][col] or []

    # Remove the marked piece from the square
    sacrifice_state["board_state"][row][col] = [
        p for p in square if not (CPU_SIDE in p.get("type", "") and p.get("marked_for_death", False))
    ] or None

    sacrifice_request = api.GameStateRequest(**sacrifice_state)
    return api.update_game_state(game_id, sacrifice_request, Response(), player=False)


def _apply_bishop_debuff_resolution(game_id: str, game_state: GameState, action: dict) -> dict:
    """Capture or spare a white piece with full bishop debuff stacks."""
    import src.api as api
    import src.cpu_search as cpu_search

    resolution_state = copy.deepcopy(game_state)
    cpu_search.mutate_for_action(game_state, resolution_state, action, CPU_SIDE)
    resolution_request = api.GameStateRequest(**resolution_state)
    return api.update_game_state(game_id, resolution_request, Response(), player=False)


def _apply_purchase(game_id: str, game_state: GameState, move: dict) -> dict:
    """Place a purchased piece on the board and send through the pipeline."""
    import src.api as api

    purchase_state = copy.deepcopy(game_state)
    to_r, to_c = move["to_pos"]
    purchase_state["board_state"][to_r][to_c] = [build_purchased_piece(move["piece_type"])]
    purchase_request = api.GameStateRequest(**purchase_state)
    return api.update_game_state(game_id, purchase_request, Response(), player=False)


def _apply_pawn_promotion(game_id: str, game_state: GameState, chosen_piece: Optional[str] = None) -> dict:
    """Replace a black pawn on row 7 with the chosen piece (random if not given)."""
    import src.api as api

    promo_state = copy.deepcopy(game_state)
    if chosen_piece is None:
        chosen_piece = random.choice(PROMOTION_PIECES)

    for col in range(8):
        square = promo_state["board_state"][7][col] or []
        for piece in square:
            if piece.get("type") == "black_pawn":
                new_piece = build_purchased_piece(f"black_{chosen_piece}")
                other_pieces = [p for p in square if p.get("type") != "black_pawn"]
                promo_state["board_state"][7][col] = other_pieces + [new_piece]
                promo_request = api.GameStateRequest(**promo_state)
                return api.update_game_state(game_id, promo_request, Response(), player=False)

    return game_state


# ---------------------------------------------------------------------------
# Game processing
# ---------------------------------------------------------------------------

def _should_use_algorithm(difficulty: str) -> bool:
    """Easy never uses the search, hard always does, medium flips a coin each turn."""
    if difficulty == DIFFICULTY_HARD:
        return True
    if difficulty == DIFFICULTY_MEDIUM:
        return random.random() < MEDIUM_ALGORITHM_PROBABILITY
    return False


def _choose_random_move(game_state: GameState) -> Optional[dict]:
    """Pick a random legal board move, occasionally a random purchase instead."""
    valid_moves = get_all_valid_moves(game_state)
    purchase_moves = _get_purchase_moves(game_state)

    if not valid_moves and not purchase_moves:
        return None

    # Prefer board moves; only consider purchases with low probability
    if valid_moves and (not purchase_moves or random.random() > PURCHASE_PROBABILITY):
        return random.choice(valid_moves)
    return random.choice(purchase_moves)


def _get_last_cpu_move(game_id: str) -> Optional[dict]:
    """Return the CPU's most recent board move as {"from", "to"}, if any is logged."""
    last_move = mongo_client["game_db"]["game_moves"].find_one(
        {"game_id": game_id, "side": CPU_SIDE}, sort=[("turn", -1)]
    )
    for moved_piece in (last_move or {}).get("moved_pieces", []):
        if CPU_SIDE in moved_piece.get("piece_type", "") and moved_piece.get("from") and moved_piece.get("to"):
            if moved_piece["from"][0] is not None and moved_piece["to"][0] is not None:
                return {"from": moved_piece["from"], "to": moved_piece["to"]}
    return None


def process_game(game_id: str, instance_id: str) -> None:
    """Process a single game: generate moves, pick one, apply it."""
    try:
        game_database = mongo_client["game_db"]
        game_state = game_database["games"].find_one({"_id": ObjectId(game_id)})
        if not game_state:
            logger.warning(f"CPU: Game {game_id} not found")
            return

        game_state["id"] = str(game_state.pop("_id"))
        version_before = game_state.get("version", 0)

        difficulty = game_state.get("cpu_difficulty", DIFFICULTY_EASY)
        use_algorithm = _should_use_algorithm(difficulty)
        promotion_piece = ALGORITHM_PROMOTION_PIECE if use_algorithm else None

        # Check if marked-for-death pieces need handling first
        if _has_marked_for_death(game_state):
            sacrifice_moves = get_marked_for_death_moves(game_state)
            if sacrifice_moves:
                if use_algorithm:
                    chosen = min(sacrifice_moves, key=lambda move: get_piece_value(move["piece_type"]))
                else:
                    chosen = random.choice(sacrifice_moves)
                logger.info(f"CPU: Sacrificing {chosen['piece_type']} at {chosen['from_pos']} in game {game_id}")
                apply_cpu_move(game_id, game_state, chosen)
                return

        # Handle pre-existing pawn on promotion rank
        if _is_pawn_promotion_needed(game_state):
            logger.info(f"CPU: Completing pawn promotion in game {game_id}")
            _apply_pawn_promotion(game_id, game_state, promotion_piece)
            return

        # A full bishop debuff stack must be resolved before any other move is legal
        debuff_targets = get_bishop_debuff_targets(game_state)
        if debuff_targets:
            if use_algorithm:
                target = max(debuff_targets, key=lambda entry: get_piece_value(entry["piece_type"]))
                resolution = "bishop_capture"
            else:
                target = random.choice(debuff_targets)
                resolution = random.choice(["bishop_capture", "bishop_spare"])
            logger.info(f"CPU: Resolving bishop debuff ({resolution}) on {target['piece_type']} at {target['from_pos']} in game {game_id}")
            _apply_bishop_debuff_resolution(game_id, game_state, {**target, "type": resolution})
            return

        if use_algorithm:
            import src.cpu_search as cpu_search
            chosen_move = cpu_search.choose_action(
                game_state,
                time_limit=HARD_THINK_SECONDS,
                last_own_move=_get_last_cpu_move(game_id),
            )
        else:
            chosen_move = _choose_random_move(game_state)

        if chosen_move is None:
            logger.info(f"CPU: No valid moves for game {game_id} (stalemate or checkmate)")
            return

        logger.info(f"CPU: Playing {chosen_move['type']} from {chosen_move.get('from_pos')} to {chosen_move.get('to_pos')} in game {game_id}")

        # Optimistic concurrency check before applying
        current = game_database["games"].find_one({"_id": ObjectId(game_id)})
        if current and current.get("version", 0) != version_before:
            logger.info(f"CPU: Game {game_id} was modified by player, skipping")
            return

        apply_cpu_move(game_id, game_state, chosen_move, promotion_piece)

    except Exception:
        logger.exception(f"CPU: Error processing game {game_id}")
    finally:
        # Clear CPU claim only if this instance still owns it
        try:
            game_database = mongo_client["game_db"]
            game_database["games"].update_one(
                {"_id": ObjectId(game_id), "cpu_id": instance_id},
                {"$set": {"cpu_id": None, "last_checked_by_cpu": None}}
            )
        except Exception as e:
            logger.error(f"CPU: Failed to release lock for game {game_id}: {e}")


# ---------------------------------------------------------------------------
# Distributed claim and polling
# ---------------------------------------------------------------------------

def claim_and_process_games(instance_id: str) -> None:
    """One polling iteration: claim games atomically, then process them in parallel."""
    game_database = mongo_client["game_db"]
    games_collection = game_database["games"]
    now = datetime.datetime.now()
    lease_cutoff = now - datetime.timedelta(seconds=CPU_LEASE_TIMEOUT_SECONDS)

    # Claim phase: atomically claim one unclaimed game at a time (bounded)
    claimed_game_ids = []
    while len(claimed_game_ids) < MAX_CLAIMS_PER_POLL:
        result = games_collection.find_one_and_update(
            {
                "turn_count": {"$mod": [2, 1]},  # odd turn = black's turn
                "black_defeat": False,
                "white_defeat": False,
                "$or": [
                    {"cpu_id": None},
                    {"cpu_id": {"$exists": False}},
                    {"last_checked_by_cpu": {"$lt": lease_cutoff}},
                ],
            },
            {
                "$set": {
                    "cpu_id": instance_id,
                    "last_checked_by_cpu": now,
                }
            },
            return_document=False,  # return the document before update
        )
        if result is None:
            break
        claimed_game_ids.append(str(result["_id"]))

    if not claimed_game_ids:
        return

    logger.info(f"CPU: Claimed {len(claimed_game_ids)} game(s) for processing")

    # Process phase: fan out to thread pool
    with ThreadPoolExecutor(max_workers=min(len(claimed_game_ids), MAX_CPU_WORKERS)) as pool:
        futures = [pool.submit(process_game, gid, instance_id) for gid in claimed_game_ids]
        for future in futures:
            try:
                future.result(timeout=CPU_GAME_TIMEOUT_SECONDS)
            except Exception as e:
                logger.error(f"CPU: Thread error: {e}")


def start_cpu_polling_loop() -> None:
    """Background polling loop — runs forever in a daemon thread."""
    instance_id = str(uuid.uuid4())
    logger.info(f"CPU polling loop started (instance: {instance_id})")

    while True:
        try:
            claim_and_process_games(instance_id)
        except Exception as e:
            logger.error(f"CPU polling error: {e}")

        time.sleep(CPU_POLL_INTERVAL_SECONDS)
