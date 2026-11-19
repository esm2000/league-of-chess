# Chess Evaluation Algorithms — Complete Research Summary
### For Building a CPU in a League of Legends-Themed Chess Variant

> **How to read this document.** Parts 1-7 are general background on chess engines, compiled
> from the chess programming literature. **Part 8 describes this game**: the actual rules
> (neutral monsters, buffs, gold), the evaluation and the search the CPU uses.

---

## PART 1: THE BIG PICTURE — What is an Evaluation Function?

An **evaluation function** (also called a *heuristic function* or *static eval*) answers the question:
> "Given a board state, how good is it for the current player?"

It returns a number. Positive = good for the player to move. Negative = bad. Zero = equal. The CPU uses this number to decide which move to make by searching ahead through possible moves and picking the one that leads to the best-evaluated position.

The foundational insight from **Claude Shannon (1949)** — the very first paper in the field — is that a computer can't calculate *all* possible moves (the game tree is too large), so it needs a function that *approximates* the value of a position without fully solving it.

---

## PART 2: THE CORE FORMULA — Shannon's Evaluation (1949)

Shannon's original formula, still the blueprint for every chess engine today:

```
f(p) = 200(K-K') + 9(Q-Q') + 5(R-R') + 3(B-B' + N-N')
       + 1(P-P') - 0.5(D-D' + S-S' + I-I') + 0.1(M-M') + ...
```

| Variable | Meaning |
|---|---|
| K, K' | Kings (you vs. opponent) |
| Q, Q' | Queens |
| R, R' | Rooks |
| B, B' | Bishops |
| N, N' | Knights |
| P, P' | Pawns |
| D, D' | Doubled pawns (penalty) |
| S, S' | Blocked pawns (penalty) |
| I, I' | Isolated pawns (penalty) |
| M, M' | Mobility (number of legal moves) |

**Key design principle:** Every pair (X vs. X') is **your value minus opponent's value**. Positive = you're ahead. This symmetric structure works with NegaMax (explained later).

---

## PART 3: THE EVALUATION COMPONENTS IN DETAIL

Modern engines break evaluation into several independent components added together (a **linear combination**). Each component is a feature × weight.

### 3.1 Material (Most Important — ~70% of eval)

The raw count of your pieces vs. theirs, multiplied by piece values.

**Standard chess values (centipawns):**
| Piece | Value |
|---|---|
| Pawn | 100 |
| Knight | 320 |
| Bishop | 330 |
| Rook | 500 |
| Queen | 900 |
| King | 20,000 (practically infinite) |

**Material imbalances to consider:**
- **Bishop pair bonus** — two bishops are stronger together (~50 centipawns bonus)
- **Redundancy penalty** — two rooks slightly weaker than rook + bishop
- **Trade-down incentive** — when ahead, exchange pieces (not pawns)
- **Lone pawn rule** — no pawns means you need +4 pawn equivalent material to win

---

### 3.2 Piece-Square Tables (PSTs)

Each piece gets a **64-entry table** (one value per board square) that adds bonuses or penalties depending on where the piece stands.

**Example: Knight table (positive = good square)**
```
-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,  0,  0,  0,  0,-20,-40,
-30,  0, 10, 15, 15, 10,  0,-30,
-30,  5, 15, 20, 20, 15,  5,-30,
-30,  0, 15, 20, 20, 15,  0,-30,
-30,  5, 10, 15, 15, 10,  5,-30,
-40,-20,  0,  5,  5,  0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50,
```
Knights are penalized on the edge and rewarded in the center.

**Implementation trick:** PSTs are incrementally updated — you only add/subtract changed values when a piece moves, making them very fast.

**Modern engines have TWO PST sets:** one for opening, one for endgame, interpolated by game phase (see Tapered Eval below).

---

### 3.3 Mobility

**Mobility = number of legal moves available to a player.**

Research by **Eliot Slater (1950)** showed a strong statistical correlation between mobility and winning. More options = more power.

**Refined approaches:**
- Count moves per piece type separately (bishop mobility ≠ rook mobility in weight)
- **Safe mobility** only: squares the piece can move to without being captured
- **Forward mobility** weighted higher than backward
- Use **bitboard popcount** for fast calculation

**Formula:**
```
mobilityScore = mobilityWeight × (yourMoves - opponentMoves)
```

---

### 3.4 King Safety

This is one of the most complex components in modern engines. A poorly defended king dramatically reduces position quality.

**Components:**
1. **Pawn Shield** — pawns near the king blocking attacks
2. **Pawn Storm** — enemy pawns advancing toward the king
3. **Attack Units** — each attacker near the king zone adds weighted pressure:

```
Minor piece (knight/bishop) attack on king zone = 2 units
Rook attack on king zone                         = 3 units
Queen attack on king zone                        = 5 units
Safe queen contact check                         = 6 units
```

4. Lookup into a **non-linear S-shaped table** — danger ramps up fast once multiple attackers converge

**Virtual Mobility trick:** Temporarily place a queen on your king's square. Count how many enemy pieces can "see" it. This estimates attacking lines.

---

### 3.5 Pawn Structure (or "Unit Formation")

Pawn structure is slow-changing and expensive to compute, so engines cache it in a **Pawn Hash Table** (95%+ hit rate).

**Penalties:**
| Feature | Description |
|---|---|
| Isolated pawn | No friendly pawns on adjacent files (penalty ~-20) |
| Doubled pawn | Two pawns on same file (penalty ~-15) |
| Backward pawn | Can't advance safely, not protected by another pawn |
| Blocked pawn | Pawn directly in front of another (penalty ~-15) |

**Bonuses:**
| Feature | Description |
|---|---|
| Passed pawn | No enemy pawn blocking or flanking — huge bonus, scales near promotion |
| Connected pawns | Two pawns defending each other |
| Pawn chain | Diagonal chain of mutually-defending pawns |

---

## PART 4: GAME PHASE AND TAPERED EVALUATION

Position values change drastically between opening and endgame. A king should hide early but activate late. Pawns become more valuable near the end.

**Tapered Evaluation formula:**
```
eval = ((opening_score × (256 - phase)) + (endgame_score × phase)) / 256
```

**Phase calculation:**
```
Phase contribution per piece:
  Pawn:   0
  Knight: 1
  Bishop: 1
  Rook:   2
  Queen:  4

totalPhase = starting maximum (calculated once)
currentPhase = totalPhase - sum of remaining pieces' values
normalizedPhase = (currentPhase × 256 + totalPhase/2) / totalPhase
```

As pieces are captured, `phase` increases from 0 (opening) toward 256 (endgame). Every evaluation term can have both an opening weight and endgame weight, smoothly interpolated.

---

## PART 5: THE SEARCH ALGORITHM — How the CPU Uses Evaluation

Evaluation alone doesn't play moves. The CPU must search ahead through possible moves.

### 5.1 Minimax

The fundamental idea: you try to maximize your score, your opponent tries to minimize it. Alternate perspectives each ply (half-move).

```
function minimax(position, depth):
    if depth == 0: return evaluate(position)
    if maximizing:
        best = -infinity
        for each move:
            best = max(best, minimax(make(move), depth-1))
        return best
    else:
        best = +infinity
        for each move:
            best = min(best, minimax(make(move), depth-1))
        return best
```

### 5.2 NegaMax (Simplified Minimax)

Since evaluation is symmetric (your good = their bad), you can simplify by always maximizing and negating the child score:

```
function negamax(position, depth):
    if depth == 0: return evaluate(position)
    best = -infinity
    for each move:
        score = -negamax(make(move), depth-1)
        best = max(best, score)
    return best
```

**This is why Shannon's formula uses (X - X') pairs** — the same function works for both sides just by negating.

### 5.3 Alpha-Beta Pruning (The Critical Optimization)

With a branching factor of b and depth d, plain minimax examines about b^d nodes. With perfect move ordering alpha-beta examines about b^(d/2): for b = 8 and d = 8 that is 8^8 ≈ 16.8 million nodes down to 8^4 = 4,096, roughly a **4,000x speedup**. (Standard chess has b ≈ 35; this variant starts around 22 for black.)

**How it works:** Maintain a window [alpha, beta]:
- **Alpha** = best score you're guaranteed so far
- **Beta** = best score your opponent is guaranteed so far

If a move leads to a score outside this window, prune the entire subtree — you don't need to look further.

```
function alphaBeta(position, depth, alpha, beta):
    if depth == 0: return evaluate(position)
    for each move:
        score = -alphaBeta(make(move), depth-1, -beta, -alpha)
        if score >= beta: return beta  // "Beta cutoff" — prune!
        if score > alpha: alpha = score
    return alpha
```

**Key insight:** The better you order moves (best moves first), the more branches get pruned. Good move ordering can effectively double your search depth.

**Enhancements:**
- **Transposition Table** — cache positions you've already evaluated (hash map)
- **Iterative Deepening** — search depth 1, then 2, then 3... Use previous results to order moves better next time
- **Aspiration Windows** — start alpha-beta with a narrow window around the expected score
- **Null Move Pruning** — skip your turn and see if the position is still good (proves a position is so good you don't need to look deeper)
- **Late Move Reductions (LMR)** — search less-promising moves at shallower depth

### 5.4 Quiescence Search (The Horizon Fix)

**Problem:** If you stop at depth 8 but the last move was a capture, your evaluation sees "free material" but doesn't see the recapture. This is the **horizon effect**.

**Solution:** At leaf nodes, don't evaluate immediately. Keep searching *captures only* until the position is "quiet" (no winning captures available).

```
function quiescence(position, alpha, beta):
    standPat = evaluate(position)  // Can "stand pat" and not capture
    if standPat >= beta: return beta
    if standPat > alpha: alpha = standPat

    for each capture (ordered by MVV-LVA):
        score = -quiescence(make(capture), -beta, -alpha)
        if score >= beta: return beta
        if score > alpha: alpha = score
    return alpha
```

**MVV-LVA (Most Valuable Victim, Least Valuable Aggressor):** Order captures so that capturing a queen with a pawn is searched before capturing a pawn with a queen.

---

## PART 6: MODERN EVALUATION — NNUE Neural Networks

**NNUE (Efficiently Updatable Neural Networks)** — introduced 2018 by Yu Nasu, adopted by Stockfish 2020 — replaced hand-crafted evaluation and dramatically increased playing strength.

### Architecture
```
Input Layer:  768 neurons
              (6 piece types × 2 colors × 64 squares)
              Binary: piece X exists on square Y? Yes/No

Hidden Layer: 1024+ neurons (the "accumulator")

Output:       Single neuron = position score
```

### The Key Innovation: Incremental Updates
Most moves only affect 2-4 input neurons. Instead of running the full network from scratch, just add/subtract the weights for changed pieces. This makes neural eval nearly as fast as hand-crafted eval.

### Training
- Supervised learning on millions of positions with known outcomes
- Loss function: minimize difference between predicted win% and actual result
- Texel Tuning (logistic regression) was the precursor to this

### Should this game use NNUE?
For a custom variant, **probably not initially.** NNUE requires massive training data. Start with hand-crafted evaluation (HCE), get it working, then optionally train a neural net later if you want stronger play.

---

## PART 7: AUTOMATED TUNING — Making Weights Optimal

### Texel's Tuning Method (2014) — The Standard

**Key idea:** Treat position evaluation as logistic regression. For a large set of positions with known outcomes (win/draw/loss), minimize the mean squared error:

```
error = (1/N) × Σ (sigmoid(eval(position)) - result)²
```

Where:
- `K` is a scaling constant (~400)
- `result` = 1.0 for win, 0.5 for draw, 0.0 for loss
- `sigmoid(x) = 1 / (1 + 10^(-x/K))` (K is applied once, inside the sigmoid)

**Process:**
1. Collect thousands of positions (from games or self-play)
2. For each weight in your eval function, nudge it +1 and -1
3. Measure which direction reduces total error
4. Repeat for all weights until convergence

### Genetic Algorithms (David, Koppel, Netanyahu 2008-2011)
- Treat evaluation weights as a "genome"
- Generate population of weight sets
- Test them against each other in games
- Keep the winners, mutate and breed
- Works well for multi-objective tuning (strength + style)

### For this game
Start with hand-tuned weights based on game knowledge. Automated tuning needs fast self-play, which this codebase does not have yet (see Part 8.5 and 8.7).

---

## PART 8: APPLYING THIS TO LEAGUE OF CHESS (CODE-GROUNDED)

Parts 1-7 are general chess-engine background. This part describes what the CPU in
this game actually does. The game is chess pieces with modified rules, neutral monsters,
buffs and gold; the code is the source of truth for those rules, and where the README
and the code disagree, the CPU follows the code.

Implementation: `backend/src/cpu_eval.py` (evaluation), `backend/src/cpu_search.py`
(search), `backend/src/cpu_player.py` (difficulty dispatch and move application).

### 8.1 Difficulty levels

| Level | Behaviour |
|---|---|
| Easy | Random legal move (occasionally a random purchase) |
| Medium | Each turn: 50% a random move, 50% the Hard algorithm |
| Hard | Always the algorithm below, about 5 seconds per move |

Difficulty is chosen when the game is created (`POST /api/game` with
`{"cpu_difficulty": ...}`) and is fixed for that game.

### 8.2 Rules that change the evaluation

Piece movement differs from chess in ways that change piece values:

- **Knights cannot jump.** Either L-shaped path must be clear, so knights are weak in
  crowded positions. Valued at 270, below a bishop.
- **Rooks have a range of 3**, growing by 1 every 5 turns from turn 15 until it covers
  the board at turn 30. Valued at 400 plus 25 per extra square of range.
- **Bishops can be captured from any adjacent square** by a piece that moves next to
  them, but they also debuff what they attack and gain energize stacks. Valued at 330.
- **Queens** stun adjacent enemies when they move without capturing, and get an extra
  move after a kill or assist. A queen can therefore take a defended piece and step away.
  Queens cannot be bought. Valued at 900.
- **Kings are never captured.** The game ends by checkmate, or by a monster killing a king.
- **File control:** one vertical move cannot run from a side's back two ranks to the
  other side's back two ranks.

Statuses the evaluation reads from each piece:

| Status | Effect in the game | Evaluation |
|---|---|---|
| `is_stunned` | Piece misses its owner's next turn | -15% of its value |
| `bishop_debuff` 1 / 2 / 3 | At 3 the bishop's owner may remove the piece | -5% / -25% / -80% |
| `energize_stacks` | At 100 a bishop captures diagonally adjacent to where it lands | +0.5 per stack, +30 at 100 |
| `marked_for_death` | Owner must surrender one marked piece | minus the cheapest marked piece |
| `check_protection` | Sword in the stone: absorbs one check | +80 per charge |

### 8.3 Neutral monsters

Monsters matter more than any positional
term because they both kill pieces and hand out the strongest buffs.

| Monster | Square | Health | Spawns on turn |
|---|---|---|---|
| Dragon | h4 | 5 | every 10th turn (10, 20, 30, ...) |
| Board Herald | a5 | 5 | 10 and 20 |
| Baron Nashor | a5 | 10 | 35, then every 15 turns |

Turns are half-moves: even turns are white's, odd turns are black's.

- **Damage:** a piece that moves onto or next to a monster deals 1 damage (2 with two or
  more dragon stacks). Pieces that were already adjacent and did not move deal none. A
  monster untouched for 6 turns heals to full.
- **Danger zone:** a piece in the 3x3 around a live monster is marked and dies two turns
  later unless it has left. The evaluation charges 90% of a piece's value once its owner
  can no longer move it out in time, and only a small tempo cost before that. Kings can
  never enter a monster's zone.
- **Spawning:** a monster spawning on an occupied square destroys what is there, and a
  king on that square loses the game. The evaluation penalises standing on h4 or a5
  within two turns of a spawn.
- **Credit:** the side whose piece lands the last hit gets the buff and 1 gold.

Buffs, as valued by the evaluation:

| Buff | Effect in the game | Value |
|---|---|---|
| Dragon, 1 stack | Pawns move and capture up to 2 squares | 40 |
| Dragon, 2 stacks | All pieces deal 2 damage to monsters | 120 |
| Dragon, 3 stacks | Pieces pass through their own pawns | 180 |
| Dragon, 4 stacks | Pieces pass through any ally; castling ignores blockers | 260 |
| Dragon, 5 stacks | For 6 turns, moving a piece marks adjacent enemies for death | 400 |
| Board Herald (8 turns) | Pawns next to the killer capture straight ahead | 60 |
| Baron Nashor (8 turns) | Pawns capture straight ahead and resist enemy pawns | 40 + 20 per pawn |

Partial damage on a monster is credited (12 per missing health point) to the side with
more pieces in its zone, so the search sees progress toward a kill before it lands.

### 8.4 Economy

- **Gold:** 1 per capture, including monster kills. Pieces cost twice their point value
  (pawn 2, knight 6, bishop 6, rook 10). Unspent gold is valued at 35 per coin, a little
  under the piece it buys, so buying is roughly neutral and is chosen when nothing better
  is available.
- **Capture point advantage:** computed from the *average* value of each side's pieces
  on the board, not the total. The leading side's pawns can capture pawns straight ahead
  at an advantage of 1 or more, and are immune to enemy pawn captures above 1. Because it
  is an average, losing pawns can raise it, so the usual "trade down when ahead" rule
  does not transfer. The evaluation reads the game's own `capture_point_advantage` field.
- **Purchases in the search:** considered only at the root, limited to the two best
  squares per affordable piece. Opponent purchases are ignored.

### 8.5 Evaluation formula

Centipawns from one side's point of view; `score(side) - score(opponent)`:

```
score(side) = Σ pieces [ material + piece-square bonus - status penalties - monster zone / spawn penalties ]
            + 35 × gold
            + dragon stack value + herald value + baron value
            + capture point advantage bonus
            - 30 if in check
            - cheapest marked-for-death piece
            + monster damage credit
```

A decided game scores ±100,000, a draw 0, and two bare kings 0. Every weight is a named
constant at the top of `cpu_eval.py`.

Not used, and why:

- **Game phase by piece count / tapered evaluation (Part 4).** Pieces can be bought back,
  so piece count does not measure progress. The clock that matters is the turn count,
  which already drives rook range and monster spawns.
- **Pawn structure terms (Part 3.5).** Forward captures from buffs and two-square pawn
  moves make doubled, blocked and isolated pawns mean something different here.
- **Mobility (Part 3.3).** Generating every move for both sides at each leaf roughly
  doubles the cost of a leaf; the time is better spent searching.
- **NNUE and automated tuning (Parts 6 and 7).** At about a millisecond per simulated
  move, the 10,000 self-play games suggested for tuning are out of reach for now.

### 8.6 Search

The depth 4-5 with a transposition table that chess engines commonly use assumes an engine
that makes and unmakes moves in microseconds. Here every move is run through the real
update pipeline (`simulate_game_update`) so that all rules apply exactly as in a live
game. That costs about 1.2 ms per move in isolation and about 2.3 ms inside the running
server.

- **Algorithm:** iterative-deepening alpha-beta with a hard time limit (5 seconds).
  From the starting position this completes a two-move lookahead and part of a third.
  If time runs out mid-iteration, moves already searched at the deeper level are used.
- **Who moves next is read from the state, not assumed.** Queen resets, surrendering a
  marked piece, resolving a full bishop debuff, pawn promotion and stun turn-skips all
  give one side consecutive actions. Plain NegaMax, which negates the score every ply,
  would be wrong here; the search maximises or minimises according to `turn_count`.
- **Forced steps are resolved inline:** promote to a queen, surrender the cheapest marked
  piece, capture (rather than spare) a piece with a full bishop debuff.
- **Quiescence (Part 5.4):** leaves are extended two plies through captures, using this
  game's captures: adjacent bishop captures, energized bishop captures and 1-health
  monsters all count.
- **Move ordering:** best move of the previous iteration first, then captures by most
  valuable victim and cheapest attacker.
- **Near-equal moves:** moves within 8 centipawns are treated as equal, and the one with
  the best immediate score is preferred, so the CPU takes a gain now rather than next
  turn. There is no repetition or 50-move rule in this game, so reversing the previous
  move is also penalised to stop piece shuffling.

Deliberately left out:

- **Null-move pruning.** It assumes passing is never better than moving. Here a piece in
  a monster zone must move or die, and stuns already skip turns, so the assumption fails.
- **Transposition table with Zobrist hashing.** The state includes turn-dependent timers,
  monster health, stacks, marks and buffs, so identical positions are rare.
- **Randomness.** The sword in the stone appears on a random square, which the search
  cannot predict; it ignores future sword spawns.

### 8.7 Ideas for later

- A faster node (copying only what a move changes, or caching attack maps) would buy
  more depth than any evaluation term.
- A CPU-versus-CPU harness for both colours would make weight tuning (Part 7) possible.
- Mobility and king-zone pressure terms, once nodes are cheap enough.

---

## PART 9: SUMMARY OF PAPERS — KEY TAKEAWAYS

| Paper | Year | Core Contribution |
|---|---|---|
| Shannon | 1949 | Material + mobility formula; minimax search framework |
| Slater | 1950 | Statistical proof that mobility correlates with winning |
| Turing | 1953 | First working chess algorithm; concept of plausible move selection |
| Berliner | 1979 | Evaluation in large domains; non-linear penalty curves |
| Frey | 1985 | Empirical weight development; test evaluation against game outcomes |
| Marsland | 1985 | Evaluation function design factors; what terms matter |
| Lee & Mahajan | 1988 | Pattern classification for evaluation learning |
| Buro | 1995 | Statistical feature combination; linear vs. nonlinear evals |
| Rollason | 2005/2012 | Hill-climbing eval; mixing MCTS with static eval |
| David et al. | 2008-2011 | Genetic algorithms for mentor-assisted eval optimization |
| Tsvetkov | 2010-2017 | Practical compilation of eval knowledge; "The Secret of Chess" |
| Yu Nasu | 2018 | NNUE — incrementally updated neural net eval |
| Stockfish NNUE | 2020 | Practical proof NNUE surpasses hand-crafted eval |

---

## PART 10: RECOMMENDED READING ORDER

1. **Start:** Read the chessprogramming.org pages on Material, Piece-Square Tables, and NegaMax — you can build a working CPU from just these.
2. **Then:** Alpha-Beta Pruning and Iterative Deepening — makes it fast enough to be practical.
3. **Then:** Quiescence Search — stops a position being judged in the middle of an exchange.
4. **Then:** Tapered Evaluation — background only; not used here (see Part 8.5).
5. **Then:** King Safety.
6. **Advanced:** Texel Tuning — when you want to automatically improve your weights.
7. **Optional:** NNUE — only if you want top-tier strength and can generate training data.

---

*Compiled from: chessprogramming.org/Evaluation and all listed publications — March 2026*
