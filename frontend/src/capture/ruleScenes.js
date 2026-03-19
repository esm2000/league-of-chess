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
    frameDelayMs: 1000,
    steps: steps.map((state) => ({ state })),
    ...extra
})

const squareRegion = (from, to, padding = 0, edgeOffset = null) => ({
    type: 'squares',
    from,
    to,
    padding,
    edgeOffset: { top: 1, left: 1, right: -1, bottom: -1, ...(edgeOffset || {}) }
})

const boardCrop = (padding = 0) => ({
    type: 'inner-board',
    padding,
    edgeOffset: { top: 1, left: 1, right: -1, bottom: -1 }
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
        squareRegion([0, 0], [2, 7]),
        createSceneState({
            boardState: createStartingBoardWithBlackAdvance()
        })
    ),
    createAnimatedScene(
        'neutral_combat1',
        squareRegion([3, 4], [7, 7], 8, { right: 40 }),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) },
                    { position: [6, 7], pieces: createPiece('white_rook') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) },
                    { position: [6, 7], pieces: createPiece('white_rook') }
                ]),
                positionInPlay: [6, 7],
                possibleMoves: [[5, 7], [4, 7], [7, 7], [6, 6], [6, 5], [6, 4]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: [createPiece('neutral_dragon', { health: 4 }), createPiece('white_rook')] }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 4 }) }
                ]),
                capturedPieces: { white: ['white_rook'], black: [] }
            })
        ]
    ),
    createAnimatedScene(
        'neutral_combat2',
        squareRegion([3, 5], [7, 7], 8, { right: 40 }),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) },
                    { position: [6, 6], pieces: createPiece('white_rook') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 7], pieces: createPiece('neutral_dragon', { health: 5 }) },
                    { position: [6, 6], pieces: createPiece('white_rook') }
                ]),
                positionInPlay: [6, 6],
                possibleMoves: [[5, 6], [4, 6], [3, 6], [7, 6], [6, 5], [6, 4], [6, 3], [6, 7]]
            }),
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
            })
        ]
    ),
    createAnimatedScene(
        'normal_pawn_movement',
        squareRegion([4, 2], [7, 4], 0, {left: 1, right: -1}),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [7, 2], pieces: createPiece('white_pawn') },
                    { position: [7, 3], pieces: createPiece('white_pawn') },
                    { position: [7, 4], pieces: createPiece('white_pawn') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [7, 2], pieces: createPiece('white_pawn') },
                    { position: [7, 3], pieces: createPiece('white_pawn') },
                    { position: [7, 4], pieces: createPiece('white_pawn') }
                ]),
                positionInPlay: [7, 3],
                possibleMoves: [[6, 3], [5, 3]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [7, 2], pieces: createPiece('white_pawn') },
                    { position: [5, 3], pieces: createPiece('white_pawn') },
                    { position: [7, 4], pieces: createPiece('white_pawn') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [7, 2], pieces: createPiece('white_pawn') },
                    { position: [5, 3], pieces: createPiece('white_pawn') },
                    { position: [7, 4], pieces: createPiece('white_pawn') }
                ]),
                positionInPlay: [5, 3],
                possibleMoves: [[4, 3]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [7, 2], pieces: createPiece('white_pawn') },
                    { position: [4, 3], pieces: createPiece('white_pawn') },
                    { position: [7, 4], pieces: createPiece('white_pawn') }
                ])
            })
        ]
    ),
    createAnimatedScene(
        'normal_pawn_combat',
        squareRegion([4, 2], [7, 5]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn') },
                    { position: [5, 4], pieces: createPiece('black_pawn') }
                ])
            }),
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
        ]
    ),
    createAnimatedScene(
        'buff1_pawn_combat',
        squareRegion([4, 2], [7, 4]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn', { pawnBuff: 1 }) },
                    { position: [5, 3], pieces: createPiece('black_knight') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [6, 3], pieces: createPiece('white_pawn', { pawnBuff: 1 }) },
                    { position: [5, 3], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [6, 3],
                possibleMoves: [[5, 3]],
                possibleCaptures: [[[5, 3], [5, 3]]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 3], pieces: createPiece('white_pawn', { pawnBuff: 1 }) }
                ]),
                capturedPieces: { white: ['black_knight'], black: [] }
            })
        ]
    ),
    createStaticScene(
        'knight_movement',
        squareRegion([3, 0], [6, 3], 0, { top: 1, bottom: -1}),
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
                { position: [5, 4], pieces: createPiece('white_rook') },
                { position: [0, 4], pieces: createPiece('black_knight') }
            ]),
            positionInPlay: [5, 4],
            possibleMoves: [[4, 4], [3, 4], [2, 4], [1, 4], [6, 4], [7, 4], [5, 3], [5, 2], [5, 1], [5, 0], [5, 5], [5, 6], [5, 7]],
            possibleCaptures: [[[0, 4], [0, 4]]]
        })
    ),
    createStaticScene(
        'bishop_movement',
        squareRegion([0, 0], [3, 3]),
        createSceneState({
            boardState: placePieces([
                { position: [2, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) }
            ]),
            positionInPlay: [2, 2],
            possibleMoves: [[0, 0], [1, 1], [3, 1], [3, 3], [1, 3]]
        })
    ),
    createAnimatedScene(
        'bishop_stacks_movement',
        squareRegion([3, 0], [6, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [5, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) }
                ]),
                positionInPlay: [5, 2],
                possibleMoves: [[4, 1], [3, 0], [4, 3], [6, 1], [6, 3]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [3, 0], pieces: createPiece('white_bishop', { energizeStacks: 35 }) }
                ])
            })
        ]
    ),
    createAnimatedScene(
        'bishop_stacks_capture',
        squareRegion([0, 0], [3, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [2, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) },
                    { position: [0, 0], pieces: createPiece('black_knight') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [2, 2], pieces: createPiece('white_bishop', { energizeStacks: 15 }) },
                    { position: [0, 0], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [2, 2],
                possibleMoves: [ [1, 1], [3, 1], [1, 3], [3, 3]],
                possibleCaptures: [[[0, 0], [0, 0]]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [0, 0], pieces: createPiece('white_bishop', { energizeStacks: 35 }) }
                ])
            })
        ]
    ),
    createAnimatedScene(
        'bishop_energized_capture',
        squareRegion([0, 0], [3, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [3, 2], pieces: createPiece('white_bishop', { energizeStacks: 100 }) },
                    { position: [1, 0], pieces: createPiece('black_pawn') },
                    { position: [1, 2], pieces: createPiece('black_pawn') }

                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [3, 2], pieces: createPiece('white_bishop', { energizeStacks: 100 }) },
                    { position: [1, 0], pieces: createPiece('black_pawn') },
                    { position: [1, 2], pieces: createPiece('black_pawn') }

                ]),
                positionInPlay: [3, 2],
                possibleMoves: [ [2, 3] ],
                possibleCaptures: [
                    [[2, 1], [1, 0]],
                    [[2, 1], [1, 2]],
                ]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [2, 1], pieces: createPiece('white_bishop', { energizeStacks: 0 }) },

                ])
            }),
        ]
    ),
    createAnimatedScene(
        'bishop_debuff',
        squareRegion([0, 0], [4, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [4, 1], pieces: createPiece('white_bishop') },
                    { position: [1, 2], pieces: createPiece('black_knight', { bishopDebuff: 2 }) }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [4, 1], pieces: createPiece('white_bishop') },
                    { position: [1, 2], pieces: createPiece('black_knight', { bishopDebuff: 2 }) }
                ]),
                positionInPlay: [4, 1],
                possibleMoves: [ [3, 0], [3, 2], [2, 3] ]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [3, 0], pieces: createPiece('white_bishop') },
                    { position: [1, 2], pieces: createPiece('black_knight', { bishopDebuff: 3 }) }
                ])
            }),
        ],
    ),
    createAnimatedScene(
        'bishop_capture',
        squareRegion([0, 0], [2, 3]),
        [
            createSceneState({
                boardState: placePieces([
                    { position: [2, 0], pieces: createPiece('white_bishop', { energizeStacks: 50 }) },
                    { position: [1, 3], pieces: createPiece('black_knight') }
                ])
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [2, 0], pieces: createPiece('white_bishop', { energizeStacks: 50 }) },
                    { position: [1, 3], pieces: createPiece('black_knight') }
                ]),
                positionInPlay: [1, 3],
                possibleCaptures: [[[2, 1], [2, 0]]],
                possibleMoves: [[0, 1]]
            }),
            createSceneState({
                boardState: placePieces([
                    { position: [2, 1], pieces: createPiece('black_knight') }
                ]),
                capturedPieces: { white: ['white_bishop'], black: [] }
            })
        ]
    ),
    createStaticScene(
        'queen_movement',
        boardCrop(),
        createSceneState({
            boardState: placePieces([
                { position: [4, 4], pieces: createPiece('white_queen') }
            ]),
            positionInPlay: [4, 4],
            possibleMoves: [
                [3, 4], [2, 4], [1, 4], [0, 4], [5, 4], [6, 4], [7, 4],
                [4, 3], [4, 2], [4, 1], [4, 0], [4, 5], [4, 6], [4, 7],
                [3, 3], [2, 2], [1, 1], [0, 0], [3, 5], [2, 6], [1, 7],
                [5, 3], [6, 2], [7, 1], [5, 5], [6, 6], [7, 7]
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
                ])
            }),
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
        ]
    ),
    createStaticScene(
        'king_movement',
        squareRegion([3, 3], [5, 5]),
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
                swordInTheStonePosition: [4, 4]
            }),
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
        ]
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
