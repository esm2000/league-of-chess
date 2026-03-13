import { useState, useEffect } from 'react';

import Background from './Background';
import Piece from './Piece';
import PossibleMove from './PossibleMove';
import Buff from './Buff';
import CapturedPieces from './CapturedPieces';
import HUD from './HUD';
import Victory from './Victory';
import Defeat from './Defeat';
import Draw from './Draw';
import PawnExchangeModal from './PawnExchangeModal';


import { GameStateContextData }  from '../context/GameStateContext';

import { PLAYERS, pickSide, snakeToCamel, useIsMobile } from '../utility';

const Board = () => {
    // positionInPlay used to figure out what piece is being moved by player
    const gameState = GameStateContextData()
    const positionInPlay = gameState.positionInPlay
    const boardState = gameState.boardState
    const possibleMoves = gameState.possibleMoves
    const possibleCaptures = gameState.possibleCaptures
    const castleMoves = gameState.castleMoves || []
    const swordInTheStonePosition = gameState.swordInTheStonePosition
    const turnCount = gameState.turnCount
    const isMobile = useIsMobile()
    const blackDefeat = gameState.blackDefeat
    const whiteDefeat = gameState.whiteDefeat

    const [shopPieceSelected, setShopPieceSelected] = useState(null)
    const [pawnExchangePosition, setPawnExchangePosition] = useState(null)

    useEffect(() => {
        if (turnCount <= 0) {
            setPawnExchangePosition(null)
            return
        }
        if (possibleMoves.length === 0 && possibleCaptures.length === 0) {
            for (let col = 0; col < 8; col++) {
                const square = boardState[0]?.[col]
                if (square?.length) {
                    const whitePawn = square.find(piece => piece.type === "white_pawn")
                    if (whitePawn) {
                        setPawnExchangePosition([0, col])
                        return
                    }
                }
            }
        }
        setPawnExchangePosition(null)
    }, [boardState, possibleMoves, possibleCaptures, turnCount])

    return(
        <div style={isMobile ? {display: "block", margin: "auto"}: null}>
            <CapturedPieces 
                side={PLAYERS[1]}
            />
            <div style={{position: 'relative'}}>
                <Background 
                    possibleCaptures={possibleCaptures}
                    shopPieceSelected={shopPieceSelected}
                    setShopPieceSelected={setShopPieceSelected}
                />
                {
                    boardState.map((pieceRow, row) => {
                        return (
                            <div key={row}>
                                {pieceRow.map((piece_array, col) => {
                                    if (piece_array?.length) {
                                        return(
                                            piece_array.map((piece, i) => {
                                                return (
                                                    <Piece
                                                        side={pickSide(piece.type)}
                                                        key={`${row}-${col}-${i}`}
                                                        row={row}
                                                        col={col}
                                                        inPlay={positionInPlay[0] === row && positionInPlay[1] === col}
                                                        type={snakeToCamel(piece.type)}
                                                        pawnBuff={piece.pawnBuff}
                                                        energizeStacks={piece.energizeStacks}
                                                        isStunned={piece.isStunned}
                                                        bishopDebuff={piece.bishopDebuff}
                                                        checkProtection={piece.checkProtection}
                                                        health={piece.health}
                                                        shopPieceSelected={shopPieceSelected}
                                                        markedForDeath={piece.markedForDeath}
                                                        // Only white king gets castle buttons; black castling is handled by AI
                                                        castleMoves={piece.type === "white_king" ? castleMoves : []}
                                                    />
                                                );
                                        }));
                                    }
                                })}
                            </div>
                        )
                    })
                }
                {!shopPieceSelected && possibleMoves.map((possibleMove) => {
                    // Filter out possible moves that overlap with capture positions
                    if (!possibleCaptures.some((possibleCapture) => JSON.stringify(possibleMove) === JSON.stringify(possibleCapture[0])))
                        return(
                            <PossibleMove
                                key={'pm' + possibleMove[0].toString() + possibleMove[1].toString()}
                                row={possibleMove[0]}
                                col={possibleMove[1]}
                                shopPieceSelected={shopPieceSelected}
                            />
                        );
                    return null;
                })}
                {swordInTheStonePosition ? 
                    <Buff
                        hide={boardState[swordInTheStonePosition[0]][swordInTheStonePosition[1]] ? true : false}
                        type='swordInTheStone'
                        row={swordInTheStonePosition[0]} 
                        col={swordInTheStonePosition[1]}
                    /> : null
                }
                {blackDefeat && whiteDefeat ?
                    <Draw isMobile={isMobile}/> : blackDefeat ?
                    <Victory isMobile={isMobile}/> : whiteDefeat ?
                    <Defeat isMobile={isMobile}/> : null
                }
                {pawnExchangePosition && (
                    <PawnExchangeModal
                        pawnPosition={pawnExchangePosition}
                        side={PLAYERS[0]}
                        onExchange={() => setPawnExchangePosition(null)}
                    />
                )}
            </div>
            <HUD
                shopPieceSelected={shopPieceSelected}
                setShopPieceSelected={setShopPieceSelected}
            />
            <CapturedPieces 
                side={PLAYERS[0]}
            />
        </div>
        
    );
}


export default Board;