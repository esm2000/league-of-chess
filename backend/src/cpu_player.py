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
from src.utils.check_checkmate import manage_check_status, trim_king_moves


CPU_POLL_INTERVAL_SECONDS = 3
CPU_LEASE_TIMEOUT_SECONDS = 20
CPU_SIDE = "black"
OPPONENT_SIDE = "white"
PROMOTION_PIECES = ["queen", "rook", "bishop", "knight"]


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


def _get_raw_moves(game_state: GameState) -> list[dict]:
    """Get all candidate moves for black pieces without king-safety filtering."""
    raw_moves = []
    prev_state = game_state.get("previous_state")

    for row in range(8):
        for col in range(8):
            square = game_state["board_state"][row][col] or []
            for piece in square:
                if CPU_SIDE not in piece.get("type", ""):
                    continue
                if piece.get("is_stunned", False):
                    continue

                moves_info = moves.get_moves(prev_state, game_state, [row, col], piece)

                if "king" in piece["type"]:
                    moves_info = trim_king_moves(moves_info, prev_state, game_state, CPU_SIDE)

                # Build a lookup for captures: to_pos -> capture_at
                capture_lookup = {}
                for cap in moves_info["possible_captures"]:
                    key = (cap[0][0], cap[0][1])
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


def _move_leaves_king_safe(game_state: GameState, move: dict) -> bool:
    """Return True if applying this move does NOT leave the black king in check."""
    simulated = copy.deepcopy(game_state)
    board = simulated["board_state"]

    from_r, from_c = move["from_pos"]
    to_r, to_c = move["to_pos"]

    if move["type"] == "castle":
        # Move king
        board[to_r][to_c] = board[from_r][from_c]
        board[from_r][from_c] = None
        # Move rook
        rook_from, rook_to = _get_castle_rook_positions(to_c)
        board[to_r][rook_to] = board[to_r][rook_from]
        board[to_r][rook_from] = None
    else:
        board[to_r][to_c] = board[from_r][from_c]
        board[from_r][from_c] = None
        if move["type"] == "capture":
            cap_r, cap_c = move["capture_at"]
            if [cap_r, cap_c] != [to_r, to_c]:
                board[cap_r][cap_c] = None

    # Check if black king is in check after this move
    old_copy = copy.deepcopy(game_state)
    manage_check_status(old_copy, simulated)
    return not simulated["check"][CPU_SIDE]


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
    """Check if any black pieces are marked for death."""
    for row in game_state["board_state"]:
        for square in row:
            for piece in square or []:
                if CPU_SIDE in piece.get("type", "") and piece.get("marked_for_death", False):
                    return True
    return False


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

def apply_cpu_move(game_id: str, game_state: GameState, move: dict) -> dict:
    """Apply a CPU move via the existing game update pipeline (select + move)."""
    import src.api as api

    if move["type"] == "sacrifice":
        return _apply_sacrifice(game_id, game_state, move)

    # Step 1: Select the piece (set position_in_play)
    select_state = copy.deepcopy(game_state)
    select_state["position_in_play"] = move["from_pos"]
    select_request = api.GameStateRequest(**select_state)
    game_after_select = api.update_game_state(game_id, select_request, Response(), player=False)

    # Step 2: Move the piece on the board
    move_state = copy.deepcopy(game_after_select)
    board = move_state["board_state"]
    from_r, from_c = move["from_pos"]
    to_r, to_c = move["to_pos"]

    if move["type"] == "castle":
        # Move king
        board[to_r][to_c] = board[from_r][from_c]
        board[from_r][from_c] = None
        # Move rook
        rook_from_col, rook_to_col = _get_castle_rook_positions(to_c)
        board[to_r][rook_to_col] = board[to_r][rook_from_col]
        board[to_r][rook_from_col] = None
    elif move["type"] == "capture":
        # Get captured piece type before overwriting
        cap_r, cap_c = move["capture_at"]
        captured_piece_type = None
        for piece in game_after_select["board_state"][cap_r][cap_c] or []:
            if OPPONENT_SIDE in piece.get("type", "") or "neutral" in piece.get("type", ""):
                captured_piece_type = piece["type"]
                break

        # Move piece
        board[to_r][to_c] = board[from_r][from_c]
        board[from_r][from_c] = None

        # Clear capture position if different from destination (en passant)
        if [cap_r, cap_c] != [to_r, to_c]:
            board[cap_r][cap_c] = None

        # Record capture
        if captured_piece_type:
            if "neutral" in captured_piece_type:
                pass  # neutral monster captures handled by pipeline
            else:
                move_state["captured_pieces"][CPU_SIDE].append(captured_piece_type)
    else:
        # Normal move
        board[to_r][to_c] = board[from_r][from_c]
        board[from_r][from_c] = None

    move_request = api.GameStateRequest(**move_state)
    game_after_move = api.update_game_state(game_id, move_request, Response(), player=False)

    # Step 3: Handle pawn promotion if needed
    if _is_pawn_promotion_needed(game_after_move):
        game_after_move = _apply_pawn_promotion(game_id, game_after_move)

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


def _apply_pawn_promotion(game_id: str, game_state: GameState) -> dict:
    """Replace a black pawn on row 7 with a randomly chosen piece."""
    import src.api as api

    promo_state = copy.deepcopy(game_state)
    chosen_piece = random.choice(PROMOTION_PIECES)

    for col in range(8):
        square = promo_state["board_state"][7][col] or []
        for i, piece in enumerate(square):
            if piece.get("type") == "black_pawn":
                new_piece = {"type": f"black_{chosen_piece}"}
                if chosen_piece == "bishop":
                    new_piece["energize_stacks"] = 0
                promo_state["board_state"][7][col] = [new_piece]
                promo_request = api.GameStateRequest(**promo_state)
                return api.update_game_state(game_id, promo_request, Response(), player=False)

    return game_state


# ---------------------------------------------------------------------------
# Game processing
# ---------------------------------------------------------------------------

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

        # Check if marked-for-death pieces need handling first
        if _has_marked_for_death(game_state):
            sacrifice_moves = get_marked_for_death_moves(game_state)
            if sacrifice_moves:
                chosen = random.choice(sacrifice_moves)
                logger.info(f"CPU: Sacrificing {chosen['piece_type']} at {chosen['from_pos']} in game {game_id}")
                apply_cpu_move(game_id, game_state, chosen)
                return

        # Generate all valid moves
        valid_moves = get_all_valid_moves(game_state)
        if not valid_moves:
            logger.info(f"CPU: No valid moves for game {game_id} (stalemate or checkmate)")
            return

        # Pick a random move
        chosen_move = random.choice(valid_moves)
        logger.info(f"CPU: Playing {chosen_move['type']} from {chosen_move.get('from_pos')} to {chosen_move.get('to_pos')} in game {game_id}")

        # Optimistic concurrency check before applying
        current = game_database["games"].find_one({"_id": ObjectId(game_id)})
        if current and current.get("version", 0) != version_before:
            logger.info(f"CPU: Game {game_id} was modified by player, skipping")
            return

        apply_cpu_move(game_id, game_state, chosen_move)

    except Exception as e:
        logger.error(f"CPU: Error processing game {game_id}: {e}")
    finally:
        # Clear CPU claim regardless of outcome
        try:
            game_database = mongo_client["game_db"]
            game_database["games"].update_one(
                {"_id": ObjectId(game_id)},
                {"$set": {"cpu_id": None, "last_checked_by_cpu": None}}
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Distributed claim and polling
# ---------------------------------------------------------------------------

def claim_and_process_games(instance_id: str) -> None:
    """One polling iteration: claim games atomically, then process them in parallel."""
    game_database = mongo_client["game_db"]
    games_collection = game_database["games"]
    now = datetime.datetime.now()
    lease_cutoff = now - datetime.timedelta(seconds=CPU_LEASE_TIMEOUT_SECONDS)

    # Claim phase: atomically claim one unclaimed game at a time
    claimed_game_ids = []
    while True:
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
    with ThreadPoolExecutor(max_workers=min(len(claimed_game_ids), 4)) as pool:
        futures = [pool.submit(process_game, gid, instance_id) for gid in claimed_game_ids]
        for future in futures:
            try:
                future.result(timeout=30)
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
