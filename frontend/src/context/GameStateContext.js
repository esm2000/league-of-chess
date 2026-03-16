import { createContext, useContext, useEffect, useRef, useState } from "react"
import { PLAYERS, BASE_API_URL, convertKeysToCamelCase, convertKeysToSnakeCase } from '../utility';

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
    queenReset: false,
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
    restartGame: () => {}
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
            if (!response.ok) {
                throw new Error(`Request failed with status code ${response.status}: ${response.statusText}`)
            }
            return response.json();
        })
        .then(jsonResponse => {
            const parsedJsonResponse = {
                ...convertKeysToCamelCase(jsonResponse),
                updateGameState: updateGameState,
                restartGame: restartGame
            }
            setGameState(parsedJsonResponse)
            sessionStorage.setItem("lastUpdated", parsedJsonResponse["lastUpdated"])
        })
        .catch(exception => {
            console.log(exception);
        });
    }

    const [gameState, setGameState] = useState(createInitialGameState);

    const fetchInProgress = useRef(false)
    const fetchGeneration = useRef(0)

    const fetchGameState = () => {
        if (fetchInProgress.current) return
        fetchInProgress.current = true
        const currentGeneration = fetchGeneration.current

        var url
        var method
        const gameStateId = sessionStorage.getItem("gameStateId")

        if (gameStateId == null) {
            url = `${BASE_API_URL}/api/game`
            method = "POST"
        } else {
            url = `${BASE_API_URL}/api/game/${gameStateId}`
            method = "GET"
        }

        fetch(url, {"method": method})
        .then(response => response.json())
        .then(result => {
            if (fetchGeneration.current !== currentGeneration) {
                fetchInProgress.current = false
                return
            }
            if (method === "POST") {
                console.log(`POST Game ID - ${result["id"]}`)
            } else {
                console.log(`GET Game ${result["id"]}`)
            }
            const parsedResult = {
                ...convertKeysToCamelCase(result),
                updateGameState: updateGameState,
                restartGame: restartGame
            }
            setGameState(parsedResult)
            sessionStorage.setItem("gameStateId", parsedResult["id"])
            sessionStorage.setItem("lastUpdated", parsedResult["lastUpdated"])
            fetchInProgress.current = false
        })
        .catch(exception => {
            console.log(exception);
            fetchInProgress.current = false
        });
    }

    const restartGame = () => {
        fetchGeneration.current += 1
        sessionStorage.removeItem("gameStateId")
        sessionStorage.removeItem("lastUpdated")
        setGameState({...createInitialGameState(), updateGameState, restartGame})
        fetchInProgress.current = false
        fetchGameState()
    }

    useEffect(() => {
        fetchGameState()
        
        const interval = setInterval(() => fetchGameState(), 3000)
        // when component is not being rendered stop refresh
        return () => {
            clearInterval(interval)
            sessionStorage.clear();
        }
    }, [])

    return(
        <GameStateContext.Provider value={gameState}>
            {children}
        </GameStateContext.Provider>
    )
}

export {
    createEmptyBoardState,
    createInitialGameState,
}

export default GameStateContext;
