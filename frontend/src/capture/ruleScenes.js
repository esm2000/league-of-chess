import { createEmptyBoardState, createInitialGameState } from '../context/GameStateContext';

const createPiece = (type, overrides = {}) => ({
    type,
    ...overrides
})

const placePieces = (placements) => {
    const boardState = createEmptyBoardState()

    placements.forEach(({ position, pieces }) => {
        const [row, col] = position
        const squarePieces = Array.isArray(pieces) ? pieces : [pieces]
        boardState[row][col] = squarePieces.map((piece) => ({ ...piece }))
    })

    return boardState
}

const createSceneState = (overrides = {}) => {
    const baseState = createInitialGameState()

    return {
        ...baseState,
        initialState: false,
        boardState: createEmptyBoardState(),
        possibleMoves: [],
        possibleCaptures: [],
        castleMoves: [],
        capturedPieces: { white: [], black: [] },
        graveyard: [],
        swordInTheStonePosition: null,
        capturePointAdvantage: null,
        blackDefeat: false,
        whiteDefeat: false,
        goldCount: { white: 0, black: 0 },
        bishopSpecialCaptures: [],
        latestMovement: {},
        queenReset: false,
        neutralAttackLog: {},
        check: { white: false, black: false },
        castleLog: {
            white: { hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false },
            black: { hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false }
        },
        neutralBuffLog: {
            white: { dragon: { stacks: 0, turn: 0 }, boardHerald: { active: false, turn: 0 }, baronNashor: { active: false, turn: 0 } },
            black: { dragon: { stacks: 0, turn: 0 }, boardHerald: { active: false, turn: 0 }, baronNashor: { active: false, turn: 0 } }
        },
        ...overrides
    }
}

const createStaticScene = (id, crop, state, extra = {}) => ({
    id,
    format: 'png',
    crop,
    frameDelayMs: 700,
    steps: [{ state }],
    ...extra
})

const createAnimatedScene = (id, crop, steps, extra = {}) => ({
    id,
    format: 'gif',
    crop,
    frameDelayMs: 700,
    steps: steps.map((state) => ({ state })),
    ...extra
})

const squareRegion = (from, to, padding = 0) => ({
    type: 'squares',
    from,
    to,
    padding
})

const boardCrop = (padding = 0) => ({
    type: 'inner-board',
    padding
})

const createStartingBoardWithBlackAdvance = () => {
    const state = createInitialGameState()
    const boardState = state.boardState.map((row) => row.map((square) => (
        square ? square.map((piece) => ({ ...piece })) : null
    )))

    boardState[1][3] = null
    boardState[2][3] = [{ type: 'black_pawn' }]

    return boardState
}

const RULE_SCENES = [
    createStaticScene(
        'center_of_board',
        squareRegion([1, 1], [6, 6]),
        createSceneState()
    ),
    createStaticScene(
        'black_start',
        squareRegion([0, 1], [3, 5]),
        createSceneState({
            boardState: createStartingBoardWithBlackAdvance()
        })
    ),
    createAnimatedScene(
        'neutral_combat1',
        squareRegion([3, 5], [7, 7], 8),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) },
                    { position: [6, 6], pieces: createPiece('white_rook') }
                ]),
                positionInPlay: [6, 6],
                possibleMoves: [[5, 6], [4, 6], [6, 7], [6, 5]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 4 }) },
                    { position: [5, 6], pieces: createPiece('white_rook') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 3 }) },
                    { position: [4, 6], pieces: createPiece('white_rook') }
                ])
            })
        ],
        { frameDelayMs: 600 }
    ),
    createAnimatedScene(
        'neutral_combat2',
        squareRegion([3, 5], [7, 7], 8),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 4 }) },
                    { position: [5, 6], pieces: createPiece('white_rook') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 4 }) }
                ]),
                capturedPieces: { white: ['white_rook'], black: [] }
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) }
                ])
            })
        ],
        { frameDelayMs: 700 }
    ),
    createAnimatedScene(
        'normal_pawn_movement',
        squareRegion([4, 2], [7, 4]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn') }
                ]),
                positionInPlay: [6, 3],
                possibleMoves: [[5, 3], [4, 3]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 3], pieces: createPiece('white_pawn') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 3], pieces: createPiece('white_pawn') }
                ]),
                positionInPlay: [5, 3],
                possibleMoves: [[4, 3]]
            })
        ],
        { frameDelayMs: 550 }
    ),
    createAnimatedScene(
        'normal_pawn_combat',
        squareRegion([4, 2], [7, 5]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn') },
                    { position: [5, 4], pieces: createPiece('black_pawn') }
                ]),
                positionInPlay: [6, 3],
                possibleMoves: [[5, 3], [4, 3]],
                possibleCaptures: [[[5, 4], [5, 4]]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 4], pieces: createPiece('white_pawn') }
                ]),
                capturedPieces: { white: ['black_pawn'], black: [] }
            })
        ],
        { frameDelayMs: 650 }
    ),
    createAnimatedScene(
        'buff1_pawn_combat',
        squareRegion([4, 2], [7, 4]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn', { pawnBuff: 1 }) },
                    { position: [5, 3], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [6, 3],
                possibleMoves: [[5, 3], [4, 3]],
                possibleCaptures: [[[5, 3], [5, 3]]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 3], pieces: createPiece('white_pawn', { pawnBuff: 1 }) }
                ]),
                capturedPieces: { white: ['black_knight'], black: [] }
            })
        ],
        { frameDelayMs: 650 }
    ),
    createStaticScene(
        'knight_movement',
        squareRegion([3, 0], [6, 3]),
        createSceneState({
            boardState: placePieces([
                { position: [5, 2], pieces: createPiece('white_knight') }
            ]),
            positionInPlay: [5, 2],
            possibleMoves: [[3, 1], [3, 3], [4, 0], [6, 0]]
        })
    ),
    createStaticScene(
        'knight_limits',
        squareRegion([3, 0], [6, 3]),
        createSceneState({
            boardState: placePieces([
                { position: [5, 2], pieces: createPiece('white_knight') },
                { position: [5, 0], pieces: createPiece('black_pawn') },
                { position: [4, 1], pieces: createPiece('white_pawn') }
            ]),
            positionInPlay: [5, 2],
            possibleMoves: [[3, 1], [3, 3]]
        })
    ),
    createStaticScene(
        'rook_movement_turn_0',
        boardCrop(),
        createSceneState({
            turnCount: 0,
            boardState: placePieces([
                { position: [5, 4], pieces: createPiece('white_rook') },
                { position: [2, 4], pieces: createPiece('black_knight') }
            ]),
            positionInPlay: [5, 4],
            possibleMoves: [[4, 4], [3, 4], [6, 4], [7, 4], [5, 3], [5, 2], [5, 1], [5, 5], [5, 6], [5, 7]],
            possibleCaptures: [[[2, 4], [2, 4]]]
        })
    ),
    createStaticScene(
        'rook_movement_turn_15',
        boardCrop(),
        createSceneState({
            turnCount: 15,
            boardState: placePieces([
                { position: [5, 4], pieces: createPiece('white_rook') },
                { position: [1, 4], pieces: createPiece('black_knight') }
            ]),
            positionInPlay: [5, 4],
            possibleMoves: [[4, 4], [3, 4], [2, 4], [6, 4], [7, 4], [5, 3], [5, 2], [5, 1], [5, 0], [5, 5], [5, 6], [5, 7]],
            possibleCaptures: [[[1, 4], [1, 4]]]
        })
    ),
    createStaticScene(
        'rook_movement_turn_20',
        boardCrop(),
        createSceneState({
            turnCount: 20,
            boardState: placePieces([
                { position: [4, 4], pieces: createPiece('white_rook') },
                { position: [0, 4], pieces: createPiece('black_knight') }
            ]),
            positionInPlay: [4, 4],
            possibleMoves: [[3, 4], [2, 4], [1, 4], [5, 4], [6, 4], [7, 4], [4, 3], [4, 2], [4, 5], [4, 6], [4, 7]],
            possibleCaptures: [[[0, 4], [0, 4]]]
        })
    ),
    createStaticScene(
        'bishop_movement',
        squareRegion([3, 0], [6, 3]),
        createSceneState({
            boardState: placePieces([
                { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) }
            ]),
            positionInPlay: [5, 2],
            possibleMoves: [[4, 1], [3, 0], [4, 3], [6, 1], [6, 3]]
        })
    ),
    createAnimatedScene(
        'bishop_stacks_movement',
        squareRegion([3, 0], [6, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) }
                ]),
                positionInPlay: [5, 2],
                possibleMoves: [[4, 1], [3, 0], [4, 3], [6, 1], [6, 3]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 3], pieces: createPiece('white_bishop', { energizeStacks: 25 }) }
                ])
            })
        ],
        { frameDelayMs: 650 }
    ),
    createAnimatedScene(
        'bishop_stacks_capture',
        squareRegion([2, 1], [5, 4]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 45 }) },
                    { position: [3, 4], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [5, 2],
                possibleCaptures: [[[3, 4], [3, 4]]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [3, 4], pieces: createPiece('white_bishop', { energizeStacks: 55 }) }
                ]),
                capturedPieces: { white: ['black_knight'], black: [] }
            })
        ],
        { frameDelayMs: 650 }
    ),
    createAnimatedScene(
        'bishop_energized_capture',
        squareRegion([2, 2], [5, 5]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 100 }) },
                    { position: [3, 4], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [5, 2],
                possibleCaptures: [
                    [[2, 3], [3, 4]],
                    [[2, 5], [3, 4]],
                    [[4, 3], [3, 4]],
                    [[4, 5], [3, 4]]
                ]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 3], pieces: createPiece('white_bishop', { energizeStacks: 0 }) }
                ]),
                capturedPieces: { white: ['black_knight'], black: [] }
            })
        ],
        { frameDelayMs: 700 }
    ),
    createAnimatedScene(
        'bishop_debuff',
        squareRegion([2, 0], [5, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 0], pieces: createPiece('white_bishop') },
                    { position: [2, 2], pieces: createPiece('black_knight', { bishopDebuff: 1 }) }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 0], pieces: createPiece('white_bishop') },
                    { position: [2, 2], pieces: createPiece('black_knight', { bishopDebuff: 2 }) }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 0], pieces: createPiece('white_bishop') },
                    { position: [2, 2], pieces: createPiece('black_knight', { bishopDebuff: 3 }) }
                ])
            })
        ],
        { frameDelayMs: 700 }
    ),
    createStaticScene(
        'bishop_capture',
        squareRegion([3, 0], [6, 3]),
        createSceneState({
            boardState: placePieces([
                { position: [5, 0], pieces: createPiece('black_bishop', { energizeStacks: 50 }) },
                { position: [4, 3], pieces: createPiece('white_knight') }
            ]),
            positionInPlay: [4, 3],
            possibleCaptures: [[[4, 1], [5, 0]]]
        })
    ),
    createStaticScene(
        'queen_movement',
        boardCrop(),
        createSceneState({
            boardState: placePieces([
                { position: [4, 3], pieces: createPiece('white_queen') },
                { position: [1, 3], pieces: createPiece('black_knight') },
                { position: [2, 5], pieces: createPiece('black_pawn') }
            ]),
            positionInPlay: [4, 3],
            possibleMoves: [
                [3, 3], [2, 3], [5, 3], [6, 3], [7, 3],
                [4, 2], [4, 1], [4, 0], [4, 4], [4, 5], [4, 6], [4, 7],
                [3, 2], [2, 1], [1, 0], [3, 4], [5, 2], [6, 1], [7, 0], [5, 4], [6, 5], [7, 6]
            ],
            possibleCaptures: [
                [[1, 3], [1, 3]],
                [[2, 5], [2, 5]]
            ]
        })
    ),
    createAnimatedScene(
        'queen_stun',
        squareRegion([2, 2], [6, 6]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 4], pieces: createPiece('white_queen') },
                    { position: [3, 3], pieces: createPiece('black_knight') },
                    { position: [3, 5], pieces: createPiece('black_rook') },
                    { position: [4, 3], pieces: createPiece('black_pawn') },
                    { position: [4, 5], pieces: createPiece('black_pawn') }
                ]),
                positionInPlay: [5, 4],
                possibleMoves: [[4, 4], [3, 4], [2, 4], [5, 3], [5, 2], [5, 5], [5, 6], [4, 3], [4, 5], [6, 3], [6, 4], [6, 5]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 4], pieces: createPiece('white_queen') },
                    { position: [3, 3], pieces: createPiece('black_knight', { isStunned: true }) },
                    { position: [3, 5], pieces: createPiece('black_rook', { isStunned: true }) },
                    { position: [4, 3], pieces: createPiece('black_pawn', { isStunned: true }) },
                    { position: [4, 5], pieces: createPiece('black_pawn', { isStunned: true }) }
                ])
            })
        ],
        { frameDelayMs: 650 }
    ),
    createStaticScene(
        'king_movement',
        squareRegion([3, 3], [6, 6]),
        createSceneState({
            boardState: placePieces([
                { position: [4, 4], pieces: createPiece('white_king') }
            ]),
            positionInPlay: [4, 4],
            possibleMoves: [[3, 3], [3, 4], [3, 5], [4, 3], [4, 5], [5, 3], [5, 4], [5, 5]]
        })
    ),
    createAnimatedScene(
        'sword_in_stone_check_protection',
        squareRegion([3, 3], [6, 5]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 4], pieces: createPiece('white_king') }
                ]),
                swordInTheStonePosition: [4, 4],
                positionInPlay: [5, 4],
                possibleMoves: [[4, 4], [4, 3], [4, 5], [5, 3], [5, 5], [6, 3], [6, 4], [6, 5]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 4], pieces: createPiece('white_king', { checkProtection: 1 }) }
                ]),
                swordInTheStonePosition: [4, 4]
            })
        ],
        { frameDelayMs: 750 }
    )
]

const RULE_SCENE_MAP = RULE_SCENES.reduce((sceneMap, scene) => {
    sceneMap[scene.id] = scene
    return sceneMap
}, {})

const getRuleScene = (sceneId) => RULE_SCENE_MAP[sceneId] || null

const getRuleSceneManifest = () => RULE_SCENES.map((scene) => ({
    id: scene.id,
    format: scene.format,
    frameDelayMs: scene.frameDelayMs,
    outputFile: `${scene.id}.${scene.format}`,
    crop: scene.crop,
    stepCount: scene.steps.length
}))

export {
    RULE_SCENES,
    getRuleScene,
    getRuleSceneManifest
}
