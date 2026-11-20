import { createContext, useContext, useEffect, useRef, useState } from "react"
import {
    PLAYERS, BASE_API_URL, CPU_DIFFICULTIES, convertKeysToCamelCase, convertKeysToSnakeCase,
    getStoredCpuDifficulty, storeCpuDifficulty
} from '../utility';

const createEmptyBoardState = () => (
    Array.from({ length: 8 }, () => Array(8).fill(null))
)

const createInitialGameState = () => ({
    initialState: true,
    turnCount: 0,
    positionInPlay: [null, null],
    boardState: [
        [[{"type":"black_pawn"}], [{"type":"black_knight"}], [{"type":"black_bishop", "energizeStacks": 0}], [{"type":"black_queen"}], [{"type":"black_king"}], [{"type":"black_bishop", "energizeStacks": 0}], [{"type":"black_knight"}], [{"type":"black_rook"}]],
        Array.from({ length: 8 }, () => [{"type":"black_pawn"}]),
        Array.from({ length: 8 }, () => null),
        Array.from({ length: 8 }, () => null),
        Array.from({ length: 8 }, () => null),
        Array.from({ length: 8 }, () => null),
        Array.from({ length: 8 }, () => [{"type":"white_pawn"}]),
        [[{"type":"white_rook"}], [{"type":"white_knight"}], [{"type":"white_bishop", "energizeStacks": 0}], [{"type":"white_queen"}], [{"type":"white_king"}], [{"type":"white_bishop", "energizeStacks": 0}], [{"type":"white_knight"}], [{"type":"white_rook"}]],
    ],
    possibleMoves: [],
    possibleCaptures: [],
    castleMoves: [],
    capturedPieces: {
        [PLAYERS[0]]: [],
        [PLAYERS[1]]: []
    },
    graveyard: [],
    swordInTheStonePosition: null,
    capturePointAdvantage: null,
    blackDefeat: false,
    whiteDefeat: false,
    goldCount: {
        [PLAYERS[0]]: 0,
        [PLAYERS[1]]: 0
    },
    bishopSpecialCaptures: [],
    latestMovement: {},
    latestSpawns: {},
    queenReset: false,
    queenResetType: null,
    neutralAttackLog: {},
    check: {
        [PLAYERS[0]]: false,
        [PLAYERS[1]]: false
    },
    castleLog: {
        white: {hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false},
        black: {hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false}
    },
    neutralBuffLog: {
        white: {dragon: {stacks:0, turn: 0}, boardHerald: {active: false, turn: 0}, baronNashor: {active: false, turn: 0}},
        black: {dragon: {stacks:0, turn: 0}, boardHerald: {active: false, turn: 0}, baronNashor: {active: false, turn: 0}}
    }
})

const GameStateContext = createContext({
    turnCount: 0,
    positionInPlay: [null, null],
    boardState: createEmptyBoardState(),
    possibleMoves: [],
    possibleCaptures: [],
    castleMoves: [],
    capturedPieces: [],
    SwordInTheStonePosition: null,
    capturePointAdvantage: null,
    blackDefeat: false,
    whiteDefeat: false,
    goldCount: null,
    bishopSpecialCaptures: [],
    latestMovement: null,
    latestSpawns: null,
    queenReset: false,
    check: {white: false, black: false},
    castleLog: {
        white: {hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false},
        black: {hasKingMoved: false, hasLeftRookMoved: false, hasRightRookMoved: false}
    },
    neutralBuffLog: {
        white: {dragon: {stacks:0, turn: 0}, boardHerald: {active: false, turn: 0}, baronNashor: {active: false, turn: 0}},
        black: {dragon: {stacks:0, turn: 0}, boardHerald: {active: false, turn: 0}, baronNashor: {active: false, turn: 0}}
    },
    restartGame: () => {},
    startGame: () => {},
    needsDifficultyChoice: false
})

export function GameStateContextData() {
    return useContext(GameStateContext)
}

// https://medium.com/@isaac.hookom/auto-refresh-data-for-react-functional-components-5eda19f912d1
// https://mtm.dev/react-child-update-context
// state refreshes every 5 second

export function GameStateProvider({children}) {
    const updateGameState = (gameState) => {
        const gameStateId = sessionStorage.getItem("gameStateId")
        
        fetch(`${BASE_API_URL}/api/game/${gameStateId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(convertKeysToSnakeCase(gameState))
        })
        .then(response => {
            if (response.status === 409) {
                updateFailCount.current += 1
                console.log(`Game state conflict (${updateFailCount.current}/3)`)
                if (updateFailCount.current >= 3) {
                    updateFailCount.current = 0
                    setReconnectMessage("Game state lost — summoning a new battle")
                    restartGame()
                }
                return
            }
            if (!response.ok) {
                throw new Error(`Request failed with status code ${response.status}: ${response.statusText}`)
            }
            updateFailCount.current = 0
            return response.json();
        })
        .then(jsonResponse => {
            if (!jsonResponse) return
            const parsedJsonResponse = {
                ...convertKeysToCamelCase(jsonResponse),
                ...actions,
                isReplaying: false,
                hasReplayHistory: jsonResponse["turn_count"] > 1
            }
            setGameState(parsedJsonResponse)
            sessionStorage.setItem("lastUpdated", parsedJsonResponse["lastUpdated"])
        })
        .catch(exception => {
            console.log(exception);
        });
    }

    const [gameState, setGameState] = useState(createInitialGameState);
    const [reconnectMessage, setReconnectMessage] = useState(null)
    // True when there is no game yet and the player has to pick a difficulty to start one
    const [needsDifficultyChoice, setNeedsDifficultyChoice] = useState(false)

    const fetchInProgress = useRef(false)
    const fetchGeneration = useRef(0)
    const isReplayingRef = useRef(false)
    const replayIntervalRef = useRef(null)
    const updateFailCount = useRef(0)
    const fetchFailCount = useRef(0)
    // Difficulty of the game in progress, reused when the game is recreated automatically
    const currentDifficulty = useRef(getStoredCpuDifficulty())

    const startReplay = () => {
        if (isReplayingRef.current) return
        const gameStateId = sessionStorage.getItem("gameStateId")
        if (!gameStateId) return

        fetch(`${BASE_API_URL}/api/game/${gameStateId}/replay`)
            .then(response => response.json())
            .then(states => {
                if (!states.length) return
                const sequence = states.map(s => convertKeysToCamelCase(s))
                isReplayingRef.current = true

                setGameState(prev => ({ ...sequence[0], ...actions, isReplaying: true, hasReplayHistory: true }))

                let stepIndex = 1
                replayIntervalRef.current = setInterval(() => {
                    if (stepIndex >= sequence.length) {
                        clearInterval(replayIntervalRef.current)
                        replayIntervalRef.current = null
                        isReplayingRef.current = false
                        // Restore current game state by re-fetching
                        fetchGameState()
                        return
                    }
                    setGameState(prev => ({ ...sequence[stepIndex], ...actions, isReplaying: true, hasReplayHistory: true }))
                    stepIndex++
                }, 1250)
            })
            .catch(e => console.log('Replay fetch error:', e))
    }

    const applyFetchedGame = (result) => {
        const parsedResult = {
            ...convertKeysToCamelCase(result),
            ...actions,
            isReplaying: false,
            hasReplayHistory: result["turn_count"] > 0
        }
        if (CPU_DIFFICULTIES.includes(parsedResult.cpuDifficulty)) {
            currentDifficulty.current = parsedResult.cpuDifficulty
        }
        setGameState(parsedResult)
        setNeedsDifficultyChoice(false)
        sessionStorage.setItem("gameStateId", parsedResult["id"])
        sessionStorage.setItem("lastUpdated", parsedResult["lastUpdated"])
    }

    // Creates a new game against a CPU of the given difficulty
    const createGame = (difficulty) => {
        fetchGeneration.current += 1
        const currentGeneration = fetchGeneration.current
        fetchInProgress.current = true
        currentDifficulty.current = difficulty

        fetch(`${BASE_API_URL}/api/game`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cpu_difficulty: difficulty })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed with status code ${response.status}: ${response.statusText}`)
            }
            return response.json()
        })
        .then(result => {
            fetchInProgress.current = false
            if (fetchGeneration.current !== currentGeneration) return
            console.log(`POST Game ID - ${result["id"]}`)
            applyFetchedGame(result)
        })
        .catch(exception => {
            console.log(exception);
            fetchInProgress.current = false
            // let the player try again from the difficulty picker
            if (fetchGeneration.current === currentGeneration) setNeedsDifficultyChoice(true)
        });
    }

    const fetchGameState = () => {
        if (isReplayingRef.current) return
        if (fetchInProgress.current) return
        const gameStateId = sessionStorage.getItem("gameStateId")

        // No game yet: wait for the player to pick a difficulty instead of creating one
        if (gameStateId == null) {
            setNeedsDifficultyChoice(true)
            return
        }

        fetchInProgress.current = true
        const currentGeneration = fetchGeneration.current

        fetch(`${BASE_API_URL}/api/game/${gameStateId}`, {"method": "GET"})
        .then(response => {
            if (!response.ok) {
                fetchFailCount.current += 1
                console.log(`Game fetch failed ${response.status} (${fetchFailCount.current}/3)`)
                if (fetchFailCount.current >= 3) {
                    fetchFailCount.current = 0
                    setReconnectMessage("Lost connection to game — starting fresh")
                    sessionStorage.removeItem("gameStateId")
                    sessionStorage.removeItem("lastUpdated")
                    createGame(currentDifficulty.current)
                    return null
                }
                fetchInProgress.current = false
                return null
            }
            fetchFailCount.current = 0
            return response.json()
        })
        .then(result => {
            if (!result) return
            fetchInProgress.current = false
            if (fetchGeneration.current !== currentGeneration || isReplayingRef.current) return
            console.log(`GET Game ${result["id"]}`)
            applyFetchedGame(result)
        })
        .catch(exception => {
            console.log(exception);
            fetchInProgress.current = false
        });
    }

    // Abandons the current game and starts a new one. Without an explicit difficulty
    // (automatic restarts after losing the game state) the current one is kept.
    const restartGame = (difficulty) => {
        const nextDifficulty = CPU_DIFFICULTIES.includes(difficulty) ? difficulty : currentDifficulty.current
        if (replayIntervalRef.current) {
            clearInterval(replayIntervalRef.current)
            replayIntervalRef.current = null
        }
        isReplayingRef.current = false
        sessionStorage.removeItem("gameStateId")
        sessionStorage.removeItem("lastUpdated")
        setGameState({
            ...createInitialGameState(),
            ...actions,
            isReplaying: false, hasReplayHistory: false
        })
        createGame(nextDifficulty)
    }

    // Starts a game from the difficulty picker and remembers the choice as the next default
    const startGame = (difficulty) => {
        storeCpuDifficulty(difficulty)
        restartGame(difficulty)
    }

    // Callbacks handed to consumers alongside the game state. Declared last: the
    // callbacks above only read it when they run, never while this component renders.
    const actions = { updateGameState, restartGame, startGame, startReplay }

    useEffect(() => {
        fetchGameState()
        
        const interval = setInterval(() => fetchGameState(), 1000)
        // when component is not being rendered stop refresh
        return () => {
            clearInterval(interval)
            sessionStorage.clear();
        }
    }, [])

    useEffect(() => {
        if (!reconnectMessage) return
        const timer = setTimeout(() => setReconnectMessage(null), 4000)
        return () => clearTimeout(timer)
    }, [reconnectMessage])

    return(
        <GameStateContext.Provider value={{ ...gameState, ...actions, reconnectMessage, needsDifficultyChoice }}>
            {children}
        </GameStateContext.Provider>
    )
}

export {
    createEmptyBoardState,
    createInitialGameState,
}

export default GameStateContext;
