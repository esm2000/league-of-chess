import React from 'react';
import { GameStateContextData } from '../context/GameStateContext';
import { IMAGE_MAP, PROMOTION_PIECES, camelToSnake, useIsMobile } from '../utility';

const PawnExchangeModal = (props) => {
    const gameState = GameStateContextData()
    const isMobile = useIsMobile()

    const handleSelection = (pieceType) => {
        if (gameState.isReplaying) return
        const newBoardState = [...gameState.boardState]
        const [row, col] = props.pawnPosition
        const square = [...(newBoardState[row][col] || [])]
        const pawnIndex = square.findIndex(p => p.type === `${props.side}_pawn`)
        if (pawnIndex !== -1) {
            square[pawnIndex] = { "type": camelToSnake(props.side + pieceType) }
        }
        newBoardState[row][col] = square

        gameState.updateGameState({
            ...gameState,
            boardState: newBoardState
        })
        props.onExchange()
    }

    return (
        <div className="modal-overlay">
            <div
                className="pixel-panel"
                style={{
                    padding: `${isMobile ? 2 : 1}vw`,
                    textAlign: 'center'
                }}
            >
                <p style={{
                    fontFamily: 'Basic',
                    fontSize: `${isMobile ? 3 : 1.5}vw`,
                    margin: `0 0 ${isMobile ? 1.5 : 0.75}vw 0`
                }}>~ Promote Pawn ~</p>
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: `${isMobile ? 2 : 1}vw`
                }}>
                    {PROMOTION_PIECES.map((piece) => (
                        <div
                            key={piece}
                            onClick={() => handleSelection(piece)}
                            style={{
                                cursor: 'pointer',
                                padding: `${isMobile ? 1 : 0.5}vw`,
                                borderRadius: `${isMobile ? 0.6 : 0.3}vw`,
                                border: `${isMobile ? 0.4 : 0.2}vw solid rgb(71, 33, 1)`,
                                backgroundColor: 'rgb(194, 164, 115)',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center'
                            }}
                        >
                            <img
                                src={IMAGE_MAP[props.side + piece]}
                                alt={piece}
                                style={{
                                    width: `${isMobile ? 8 : 4}vw`,
                                    imageRendering: 'pixelated'
                                }}
                            />
                            <p style={{
                                fontFamily: 'Basic',
                                fontSize: `${isMobile ? 1.5 : 0.75}vw`,
                                margin: `${isMobile ? 0.5 : 0.25}vw 0 0 0`,
                                color: 'rgb(71, 33, 1)'
                            }}>{piece}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default PawnExchangeModal;
