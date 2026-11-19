# Architecture Reference

Last Updated: 2026-11-18

Detailed module and structure reference for League of Chess. For conventions and workflow, see [CLAUDE.md](../CLAUDE.md). For game rules, see [README.md](../README.md).

## Directory Structure

```
more-chess/
├── backend/
│   ├── src/
│   │   ├── api.py               # FastAPI route definitions
│   │   ├── cpu_player.py        # CPU polling loop, difficulty dispatch, move application
│   │   ├── cpu_eval.py          # CPU static evaluation (variant-aware)
│   │   ├── cpu_search.py        # CPU lookahead search (alpha-beta over the real pipeline)
│   │   ├── types.py             # TypedDicts and type aliases
│   │   ├── moves/               # Move generation package (one module per piece type)
│   │   │   ├── __init__.py      # Dispatcher (get_moves()) + re-exports
│   │   │   ├── _helpers.py      # Shared move generation helpers
│   │   │   ├── pawn.py
│   │   │   ├── knight.py
│   │   │   ├── bishop.py
│   │   │   ├── rook.py
│   │   │   ├── queen.py
│   │   │   └── king.py
│   │   ├── database.py          # MongoDB connection
│   │   ├── log.py               # Logging
│   │   └── utils/               # Game logic utilities
│   │       ├── __init__.py      # Re-exports + error message constants
│   │       ├── board_analysis.py
│   │       ├── castle_mechanics.py
│   │       ├── check_checkmate.py
│   │       ├── game_ending.py
│   │       ├── game_scoring.py
│   │       ├── game_state.py
│   │       ├── game_update_pipeline.py
│   │       ├── monsters.py
│   │       ├── moves_and_positions.py
│   │       ├── piece_mechanics.py
│   │       ├── queen_mechanics.py
│   │       ├── special_items.py
│   │       ├── stun_mechanics.py
│   │       └── validation.py
│   ├── tests/
│   │   ├── unit/                # Unit tests (piece move generation)
│   │   ├── integration/         # Integration tests (full API flows)
│   │   │   └── conftest.py      # Pytest fixtures for game setup/teardown
│   │   └── test_utils.py
│   ├── mocks/                   # Test mock game states
│   ├── server.py                # Entry point
│   ├── requirements.txt
│   └── Dockerfile               # Backend container
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React UI components
│   │   ├── context/GameStateContext.js  # Global state + API sync
│   │   ├── assets/              # Images (pieces, rules, statuses)
│   │   ├── index.js             # Entry point
│   │   └── utility.js           # Helper functions
│   ├── package.json
│   ├── Dockerfile               # Frontend container (multi-stage with nginx)
│   └── nginx.conf               # Nginx config with /api/ proxy to backend
│
├── docker compose.yml          # Full stack orchestration (mongo + backend + frontend)
├── .env                        # Local env vars (gitignored)
├── .env.example                # Env var template
└── README.md
```

## Backend Modules

| Module | Responsibility |
|--------|---------------|
| `src/api.py` | FastAPI routes for game CRUD operations |
| `src/cpu_player.py` | Background CPU (black): claims games, picks a move by difficulty (`easy` random, `medium` 50/50, `hard` search), resolves forced steps (surrender, promotion, bishop debuff), applies moves through the API pipeline |
| `src/cpu_eval.py` | `evaluate(game_state, side)`: centipawn score from material, piece-square tables, piece statuses, neutral monsters and buffs, gold, capture point advantage. Weights are constants at the top of the file |
| `src/cpu_search.py` | `choose_action()`: iterative-deepening alpha-beta with capture quiescence and a time limit. Builds child states with `simulate_game_update`, reads the side to move from `turn_count`, resolves forced steps inline |
| `src/log.py` | Root logger; `suppress_logging()` silences the current thread while the CPU search simulates moves |
| `src/utils/__init__.py` | Re-exports, error message constants |
| `src/types.py` | TypedDicts & type aliases (`GameState`, `Piece`, `MoveResult`, `Position`, `BoardState`) |
| `src/moves/__init__.py` | `get_moves()` dispatcher; per-piece modules in same package |
| `src/moves/_helpers.py` | Shared helpers (file control, dragon buff, baron immunity) |
| `src/database.py` | MongoDB connection, exports `mongo_client` |
| `utils/game_update_pipeline.py` | Turn orchestration: `prepare_game_update`, `apply_special_piece_effects`, `manage_turn_progression`, `validate_moves_and_pieces`, `handle_endgame_conditions` |
| `utils/check_checkmate.py` | `is_in_check`, `is_checkmate`, `is_stalemate`, `trim_king_moves` |
| `utils/piece_mechanics.py` | Bishop energize, Divine Right, marked-for-death |
| `utils/queen_mechanics.py` | Queen stun & turn reset |
| `utils/monsters.py` | Monster spawning, damage, buff application |
| `utils/validation.py` | API input validation |
| `utils/castle_mechanics.py` | Castling validation |
| `utils/game_scoring.py` | Gold economy (+1g to King per ally capture) |
| `utils/game_ending.py` | Win/loss/draw detection |
| `utils/game_state.py` | Default structure for new games |
| `utils/board_analysis.py` | Position evaluation, monster slain position |
| `utils/moves_and_positions.py` | Bounds check, path clearance |
| `utils/special_items.py` | Sword pickup, piece purchase |
| `utils/stun_mechanics.py` | Stun tracking, skips stunned pieces |

## Frontend Modules

| Module | Responsibility |
|--------|---------------|
| `components/Board.js` | Game board, piece interactions, move highlighting |
| `components/Piece.js` | Piece rendering, drag-and-drop, buff indicators |
| `components/DifficultySelect.js` | Easy / Medium / Hard buttons, used by the pre-game overlay in `Board.js` and the Restart row in `HUD.js` |
| `context/GameStateContext.js` | Global state + API sync (`updateGameState`, `fetchGameState`, `startGame(difficulty)`, `restartGame`). No game is created until the player picks a difficulty (`needsDifficultyChoice`) |
| `utility.js` | Shared helpers: `pickSide`, `snakeToCamel`, `BASE_API_URL` |

## Game State Shape

See `backend/src/types.py` for the authoritative `GameState` TypedDict. Key structural notes:

- `board_state[row][col]`: row 0 = black's back rank, row 7 = white's back rank
- Each cell is an **array** of piece objects (supports monster co-occupancy)
- Piece objects have mandatory `type` (e.g., `"white_pawn"`) and optional buff fields
- Positions always `[row, col]`; colors always lowercase (`"white"`, `"black"`, `"neutral"`)

## Move Generation Return Format

All `get_moves_for_*()` functions return:

```python
{
    "possible_moves": [[row, col], ...],
    "possible_captures": [[[r1, c1], [r2, c2]], ...],   # [move_to, capture_at]
    "threatening_move": [[row, col], ...],    # squares attacked (for check detection, not shown to player)
    "castle_moves": [[row, col], ...]         # King only; empty for other pieces
}
```

Functions take `curr_game_state`, `prev_game_state`, `curr_position`. Unused keys return `[]`.

## Test Structure

- **Unit tests** (`tests/unit/`): use `mocks/empty_game.py`, direct `moves.get_moves()` calls, no DB
- **Integration tests** (`tests/integration/`): use `mocks/starting_game.py`, FastAPI test client, `select_and_move_*()` helpers from `test_utils.py`
- Each test uses fresh `copy.deepcopy()` mock states; fixtures in `conftest.py`

### ASCII Board Diagram Convention (unit tests)
- First row of diagrams = white case (`side='white'`)
- Second row = black case (`side='black'`)
- A second column is only used when showing piece movement (before -> after)
- Abbreviations: `wp` (white pawn), `bp` (black pawn), `wk` (white knight), `bk` (black knight), `wK` (white king), `bK` (black king), `wb` (white bishop), `wr` (white rook), `wQ` (white queen), `nd` (neutral dragon), `ss` (sword in stone)
