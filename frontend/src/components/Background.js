import React, { useState } from 'react';
import '../index.css';

import { GameStateContextData }  from '../context/GameStateContext';

import {
    determineBackgroundColor,
    determineColor,
    useIsMobile,
    DRAGON_POSITION,
    BOARD_HERALD_POSITION,
    BARON_NASHOR_POSITION,
    PLAYERS,
    IMAGE_MAP,
    camelToSnake,
    UNSAFE_KING_SQUARE_COLOR
} from '../utility';

const isBossActive = (boardState, bossPosition, bossType) => {
    return !boardState[bossPosition[0]][bossPosition[1]] ? 
        false :
    boardState[bossPosition[0]][bossPosition[1]].some((piece) => piece.type === bossType)
}

const Square = (props) => {
    const row = props.row
    const col = props.col
    const gameState = GameStateContextData();
    const boardState = gameState.boardState
    const isDragonActive = isBossActive(gameState.boardState, DRAGON_POSITION, "neutral_dragon")
    const isHeraldActive = isBossActive(gameState.boardState, BOARD_HERALD_POSITION, "neutral_board_herald")
    const isBaronActive = isBossActive(gameState.boardState, BARON_NASHOR_POSITION, "neutral_baron_nashor")
    const positionInPlay = gameState.positionInPlay
    const possibleCaptures = gameState.possibleCaptures
    const swordInTheStonePosition = gameState.swordInTheStonePosition

    const backgroundColor = determineBackgroundColor(row, col, positionInPlay, possibleCaptures, isDragonActive, isHeraldActive, isBaronActive, swordInTheStonePosition)
    const color = determineColor(row, col, isDragonActive, isHeraldActive, isBaronActive)
    const isMobile = useIsMobile()

    const isValidSquare = (row, col) => {
        if (row <= 3) {
            return false
        }
        const bossPositions = []
        if (isDragonActive) bossPositions.push(DRAGON_POSITION)
        if (isHeraldActive) bossPositions.push(BOARD_HERALD_POSITION)
        if (isBaronActive) bossPositions.push(BARON_NASHOR_POSITION)
        
        for (let i = 0; i < bossPositions.length; i++) {
            if ([0, 1].includes(Math.abs(row - bossPositions[i][0])) && [0, 1].includes(Math.abs(col - bossPositions[i][1]))) {
                return false
            }
        }

        if (JSON.stringify([row, col]) === JSON.stringify(swordInTheStonePosition)){
            return false
        }

        if (boardState[row][col]?.length) {
            return false
        }
    
        return true
    }

    const handleSquareSelectionClick = () => {
        if (gameState.isReplaying) return
        const newBoardState = [...gameState.boardState]

        if (!newBoardState[row][col]?.length) {
            newBoardState[row][col] = [{"type": camelToSnake(props.shopPieceSelected)}]
        } else {
            // player shouldn't be allowed to place piece where another piece is present
            return
        }

        gameState.updateGameState({
            ...gameState,
            boardState: newBoardState,
        })
        props.setShopPieceSelected(null)
    }

    const handleSquareClick = () => {
        if (gameState.isReplaying) return
        if (positionInPlay?.[0] != null && positionInPlay?.[1] != null) {
            const newBoardState = [...gameState.boardState]
            const newPositionInPlay = [null, null]
            const pieceInPlay = newBoardState[positionInPlay[0]][positionInPlay[1]].find(piece => piece.type.includes(PLAYERS[0]))
            if (pieceInPlay) {
                if (newBoardState[row][col]) {
                    newBoardState[row][col].push(pieceInPlay)
                } else {
                    newBoardState[row][col] = [pieceInPlay]
                }
                newBoardState[positionInPlay[0]][positionInPlay[1]] = newBoardState[positionInPlay[0]][positionInPlay[1]]?.filter(piece => piece.type !== pieceInPlay.type)
            }
            gameState.updateGameState({
                ...gameState, 
                boardState: newBoardState,
                positionInPlay: newPositionInPlay
            })
        }
    }

    const [isHovering, setIsHovering] = useState(false)
    const showHighlight = props.shopPieceSelected && isValidSquare(row, col)
    const unsafeKingMoves = gameState.unsafeKingMoves || []
    const isUnsafe = unsafeKingMoves.some(m => m[0] === row && m[1] === col)

    return (
        <div
            data-square={`${row}-${col}`}
            style={{ backgroundColor, position: 'relative' }}
            className="square"
            onClick={() => handleSquareClick()}
        >
            {isUnsafe && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    backgroundColor: UNSAFE_KING_SQUARE_COLOR,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    pointerEvents: 'none',
                    zIndex: 1
                }}>
                    <span style={{
                        fontSize: `${isMobile ? 4 : 2}vw`,
                        fontWeight: 'bold',
                        color: 'rgba(186, 0, 0, 0.6)',
                        lineHeight: 1,
                        userSelect: 'none'
                    }}>✕</span>
                </div>
            )}
            {showHighlight && (
                <div
                    className="valid-square-highlight"
                    onClick={(e) => { e.stopPropagation(); handleSquareSelectionClick(); }}
                    onMouseEnter={() => setIsHovering(true)}
                    onMouseLeave={() => setIsHovering(false)}
                />
            )}
            {showHighlight && isHovering && (
                <img
                    src={IMAGE_MAP[props.shopPieceSelected]}
                    className="ghost-piece"
                    alt="preview"
                    style={{ width: `${isMobile ? 3.6 : 1.8}vw`, height: `${isMobile ? 5.9 : 2.95}vw` }}
                />
            )}
        </div>
    )
}


const Row = (props) => {
    return (
        <div style={{ display: 'flex', flexDirection: "row" }}>
            {
                new Array(8).fill(0).map((_, i) => (
                    <Square 
                        key={i} 
                        row={props.row} 
                        col={i}
                        shopPieceSelected={props.shopPieceSelected}
                        setShopPieceSelected={props.setShopPieceSelected}    
                    />
                ))
            }
        </div>
    );
}


const Background = (props) => {
    return (
        <div style={{ display: 'flex', flexDirection: "column" }}>
            {
                new Array(8).fill(0).map((_, i) => (
                    <Row 
                        key={i} 
                        row={i} 
                        shopPieceSelected={props.shopPieceSelected}
                        setShopPieceSelected={props.setShopPieceSelected}    
                    />
                ))
            }
        </div>
    );
}


export default Background;
