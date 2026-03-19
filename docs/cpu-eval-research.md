# Chess Evaluation Algorithms — Complete Research Summary
### For Building a CPU in a League of Legends-Themed Chess Variant

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

### For your LoL variant:
Replace piece types with LoL unit classes. Assign base "gold values" or power ratings to each champion. The formula adapts naturally — you're still computing "my power minus their power."

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

**For LoL:** Assign each champion a "power value" based on their role. Carries might be worth more, but tanks might have defensive bonuses that modify their effective value contextually.

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

**For LoL:** Each champion has preferred zones on the "map." A mage might prefer the back row. A bruiser prefers the front. PSTs encode this naturally.

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

**For LoL:** Mobility could represent abilities available, range coverage, or attack options. Units with more "reach" get bonuses.

---

### 3.4 King Safety (or "Base Safety" in your variant)

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

**For LoL:** Replace "king" with your Nexus or high-value unit. The attack units concept maps perfectly to champions in range/zone of your base.

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

**For LoL:** Unit formation bonuses/penalties. Clumped units might be vulnerable to AoE. Isolated units might be weaker. Units protecting each other get synergy bonuses.

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

**For LoL:** Early game vs. late game is literally a core LoL concept. Early game = board control, positioning, ability uptime. Late game = raw power scaling, 1v1 potential. Tapered eval models this perfectly.

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

Without pruning, depth-8 search might examine 8^8 = 16 million nodes. Alpha-beta cuts this to roughly 8^4 = 4,096 nodes with perfect move ordering — a **10,000x speedup**.

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

**For LoL:** Quiescence search is essential in any game where combats resolve over multiple steps. Your "combat resolution" phase is effectively quiescence search territory.

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

### Should you use NNUE for your game?
For a custom variant, **probably not initially.** NNUE requires massive training data. Start with hand-crafted evaluation (HCE), get it working, then optionally train a neural net later if you want stronger play.

---

## PART 7: AUTOMATED TUNING — Making Weights Optimal

### Texel's Tuning Method (2014) — The Standard

**Key idea:** Treat position evaluation as logistic regression. For a large set of positions with known outcomes (win/draw/loss), minimize the mean squared error:

```
error = (1/N) × Σ (sigmoid(eval(position) / K) - result)²
```

Where:
- `K` is a scaling constant (~400)
- `result` = 1.0 for win, 0.5 for draw, 0.0 for loss
- `sigmoid(x) = 1 / (1 + 10^(-x/K))`

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

### For LoL variant:
Start with hand-tuned weights based on game knowledge. Use automated tuning after you have working self-play. Even simple gradient descent over 100K self-play games will dramatically improve strength.

---

## PART 8: APPLYING ALL OF THIS TO YOUR LOL CHESS VARIANT

### Step 1: Define Your "Pieces" (Champions)

Each champion needs:
- **Base power value** (material score equivalent)
- **Position table** (where on the board are they strongest?)
- **Opening vs. endgame weights** (early game vs. late game strength)
- **Special abilities** (modifiers to normal eval rules)

### Step 2: Define Your Evaluation Terms

Adapt Shannon's formula for your game:

```
eval = championValues
     + positionBonuses (PST)
     + mobilityScore
     + safetyScore (nexus/base safety)
     + synergyBonuses (e.g., team comps)
     - weaknessesScore (isolated units, bad positioning)
     + gamePhaseAdjustments (early/late game scaling)
```

### Step 3: Implement NegaMax + Alpha-Beta

Start here. It's ~100 lines of code and gives you a working CPU immediately. Depth 4-5 will feel competent to most players.

```
Recommended stack:
- NegaMax with Alpha-Beta
- Transposition table (Zobrist hashing)
- Iterative deepening
- Quiescence search for combat resolution
- Move ordering (captures first, then positional moves)
```

### Step 4: Add Game-Phase Awareness

Since LoL has explicit early/late game scaling (champion power curves), tapered evaluation is a natural fit. Define:
- `openingWeight` = early game strength
- `endgameWeight` = late game scaling
- Phase = based on items/gold/time (your game's equivalent of piece count)

### Step 5: Special LoL Mechanics

For rules unique to your game, the evaluation needs custom terms:
- **Crowd Control** — units that can stun/slow attackers: add safety bonus
- **Range** — ranged units cover more of the board: mobility bonus
- **Sustain** (healing/lifesteal) — endurance in prolonged fights: combat eval term
- **Burst damage** — can one-shot enemy carries: prioritize targeting
- **Team compositions** — if you have champion synergies (like TFT traits): explicit synergy bonus terms

### Step 6: Tune Your Weights

1. Hard-code initial weights from LoL balance knowledge
2. Play 10,000 CPU-vs-CPU games
3. Apply Texel-style logistic regression to optimize
4. Repeat

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

## PART 10: RECOMMENDED READING ORDER (for your use case)

1. **Start:** Read the chessprogramming.org pages on Material, Piece-Square Tables, and NegaMax — you can build a working CPU from just these.
2. **Then:** Alpha-Beta Pruning and Iterative Deepening — makes it fast enough to be practical.
3. **Then:** Quiescence Search — essential for any game with multi-step combat.
4. **Then:** Tapered Evaluation — for your early/late game scaling.
5. **Then:** King Safety — adapt for Nexus/base safety.
6. **Advanced:** Texel Tuning — when you want to automatically improve your weights.
7. **Optional:** NNUE — only if you want top-tier strength and can generate training data.

---

*Compiled from: chessprogramming.org/Evaluation and all listed publications — March 2026*
