import React from 'react';

import  { updateGameState, GameStateContextData }  from '../context/GameStateContext';

import { 
    PLAYERS, 
    IMAGE_MAP, 
    MAX_BOSS_HEALTH, 
    useIsMobile, 
    snakeToCamel,
    camelToSnake
} from '../utility';

const Piece = (props) => {
    const gameState = GameStateContextData()
    const positionInPlay = gameState.positionInPlay
    const isMobile = useIsMobile()
    const topPosition = props.row * 3.7 * (isMobile ? 2: 1)
    const leftPosition = props.col * 3.7 * (isMobile ? 2: 1)

    const handlePieceClick = () => {
        if (props.shopPieceSelected) return

        const isNeutralPiecePresent = () => {
            if (props.side === "neutral") return true
            const square = gameState.boardState[props.row]?.[props.col] || []
            return square.some(piece => piece.type.includes("neutral"))
        }

        const capturePiece = (type) => {
            const pieceInPlay = gameState.boardState[positionInPlay[0]][positionInPlay[1]].find(piece => piece.type.includes(PLAYERS[0]))
            const newCapturedPieces = {
                ...gameState.capturedPieces,
                [PLAYERS[0]]: [
                    ...gameState.capturedPieces[PLAYERS[0]],
                    ...gameState.boardState[props.row][props.col]
                        .filter(piece => snakeToCamel(piece?.type) === type)
                        .map(piece => piece.type)
                ]
            }

            const newBoardState = gameState.boardState.map((row, r) => {
                if (r !== props.row && r !== positionInPlay[0]) return row;
                return row.map((square, c) => {
                    if (!square) return square;
                    if (r === props.row && c === props.col) {
                        const filtered = square.filter(piece => !piece.type.includes(PLAYERS[1]) && snakeToCamel(piece?.type) !== type)
                        return [...filtered, pieceInPlay]
                    }
                    if (r === positionInPlay[0] && c === positionInPlay[1]) {
                        return square.filter(piece => piece.type !== pieceInPlay.type)
                    }
                    return square;
                });
            });

            gameState.updateGameState({
                ...gameState,
                capturedPieces: newCapturedPieces,
                boardState: newBoardState,
                positionInPlay: [null, null]
            })
        }
        
        if (props.side === PLAYERS[0] && !props.isStunned) {
            if(
                gameState.positionInPlay.toString() === [null, null].toString() || 
                (gameState.positionInPlay[0] !== props.row || gameState.positionInPlay[1] !== props.col)
            ) {
                gameState.updateGameState({...gameState, positionInPlay: [props.row, props.col]})
            } else if(gameState.positionInPlay[0] === props.row && gameState.positionInPlay[1] === props.col) {
                gameState.updateGameState({...gameState, positionInPlay: [null, null]})
            }
        }
        else if (props.side === PLAYERS[1] && positionInPlay?.[0] != null && positionInPlay?.[1] != null) {
            capturePiece(props.type)
        }

        // scenario 0 - a neutral monster is present with another friendly piece and there's no piece in play make it the piece in play
        else if (
            isNeutralPiecePresent() && 
            positionInPlay?.[0] === null &&
            positionInPlay?.[1] === null &&
            gameState.boardState[props.row][props.col].some((piece) => piece.type.includes(PLAYERS[0]))
        ) {
            gameState.updateGameState({...gameState, positionInPlay: [props.row, props.col]})

        }

        else if (isNeutralPiecePresent() && positionInPlay?.[0] != null && positionInPlay?.[1] != null) {
            const pieceInPlay = gameState.boardState[positionInPlay[0]][positionInPlay[1]].find(piece => piece.type.includes(PLAYERS[0]))

            // scenario 1 - only a neutral monster is present with greater than 1 health
            // scenario 2 - only a neutral monster is present with 1 health
            if (gameState.boardState[props.row][props.col].length == 1) {
                // damage handled by backend
                const newBoardState = gameState.boardState.map((row, r) => {
                    if (r !== props.row && r !== positionInPlay[0]) return row;
                    return row.map((square, c) => {
                        if (!square) return square;
                        if (r === props.row && c === props.col) {
                            return [...square, pieceInPlay]
                        }
                        if (r === positionInPlay[0] && c === positionInPlay[1]) {
                            return square.filter(piece => !piece.type.includes(PLAYERS[0]))
                        }
                        return square;
                    });
                });
                gameState.updateGameState({
                    ...gameState,
                    boardState: newBoardState,
                    positionInPlay: [null, null]
                })
            }
            // scenario 3 - a neutral monster is present with greater than 1 health and another piece is present
            // scenario 4 - a neutral monster is present with 1 health and another piece is present
            else {
                // if the piece is friendly do nothing
                const square = gameState.boardState[props.row][props.col]
                // if the piece is an enemy piece capture it and damage the neutral monster
                // damage/capture on neutral monster handled by backend
                const enemyPiece = square.find(piece => piece.type.includes(PLAYERS[1]))
                
                if (enemyPiece) capturePiece(enemyPiece.type)
            }

            
        }   
    }

    const handleSpareButtonClick = () => {
        const newBoardState = gameState.boardState.map((row, r) => {
            if (r !== props.row) return row;
            return row.map((square, c) => {
                if (c !== props.col || !square) return square;
                return square.map(piece =>
                    snakeToCamel(piece?.type) === props.type
                        ? { ...piece, bishopDebuff: 0 }
                        : piece
                );
            });
        });

        gameState.updateGameState({
            ...gameState,
            boardState: newBoardState
        })
    }

    const handleCaptureButtonClick = () => {
        const square = gameState.boardState[props.row][props.col] || []
        const captured = square.filter(piece => snakeToCamel(piece?.type) === props.type).map(piece => piece.type)
        const newCapturedPieces = {
            ...gameState.capturedPieces,
            [PLAYERS[0]]: [...gameState.capturedPieces[PLAYERS[0]], ...captured]
        }

        const newBoardState = gameState.boardState.map((row, r) => {
            if (r !== props.row) return row;
            return row.map((sq, c) => {
                if (c !== props.col || !sq) return sq;
                return sq.filter(piece => snakeToCamel(piece?.type) !== props.type);
            });
        });

        const newBishopSpecialCaptures = [
            {
                position: [props.row, props.col],
                type: camelToSnake(props.type)
            }
        ]

        gameState.updateGameState({
            ...gameState,
            bishopSpecialCaptures: newBishopSpecialCaptures,
            boardState: newBoardState,
            capturedPieces: newCapturedPieces,
        })
    }

    const handleCastleButtonClick = (castleMove) => {
        const startRow = castleMove[0]
        const kingCol = props.col
        const targetKingCol = castleMove[1]

        const isQueenside = targetKingCol === 2
        const rookFromCol = isQueenside ? 0 : 7
        const rookToCol = isQueenside ? 3 : 5

        const newBoardState = gameState.boardState.map((row, r) => {
            if (r !== startRow) return row;
            return row.map((square, c) => {
                if (c === targetKingCol) return row[kingCol]
                if (c === kingCol) return null
                if (c === rookToCol) return row[rookFromCol]
                if (c === rookFromCol) return null
                return square;
            });
        });

        gameState.updateGameState({
            ...gameState,
            boardState: newBoardState,
            positionInPlay: [null, null],
            castleLog: {
                ...gameState.castleLog,
                white: {
                    ...gameState.castleLog.white,
                    hasKingMoved: true,
                    hasLeftRookMoved: isQueenside ? true : gameState.castleLog.white.hasLeftRookMoved,
                    hasRightRookMoved: !isQueenside ? true : gameState.castleLog.white.hasRightRookMoved,
                }
            }
        })
    }

    const handleSurrenderButtonClick = () => {
        const square = gameState.boardState[props.row][props.col] || []
        const surrendered = square.find(piece => snakeToCamel(piece?.type) === props.type)
        if (!surrendered) return

        const newCapturedPieces = {
            ...gameState.capturedPieces,
            [PLAYERS[1]]: [...gameState.capturedPieces[PLAYERS[1]], surrendered.type]
        }

        let removed = false
        const newBoardState = gameState.boardState.map((row, r) => {
            if (r !== props.row) return row;
            return row.map((sq, c) => {
                if (c !== props.col || !sq) return sq;
                return sq.filter(piece => {
                    if (!removed && snakeToCamel(piece?.type) === props.type) {
                        removed = true
                        return false
                    }
                    return true
                });
            });
        });

        gameState.updateGameState({
            ...gameState,
            boardState: newBoardState,
            capturedPieces: newCapturedPieces,
        })
    }

    const pickClassName = () => {
        if (props.side !== 'neutral') return 'regular_piece'
        if (props.type.toLowerCase().includes('dragon')) return 'dragon_piece'
        if (props.type.toLowerCase().includes('herald')) return 'herald_piece'
        if (props.type.toLowerCase().includes('nashor')) return 'nashor_piece'
    }

    const pieceActionBtnStyle = (topOffset, leftOffset, borderColor, bgColor) => ({
        top: `${topPosition + topOffset}vw`,
        left: `${leftPosition + leftOffset}vw`,
        borderRadius: `${0.3 * (isMobile ? 2 : 1)}vw`,
        padding: `${0.1 * (isMobile ? 2 : 1)}vw ${0.3 * (isMobile ? 2 : 1)}vw`,
        whiteSpace: 'nowrap',
        position: 'absolute',
        textAlign: 'center',
        textDecoration: 'none',
        outline: 'none',
        cursor: 'pointer',
        borderColor,
        color: 'white',
        backgroundColor: bgColor,
    })

    const buffedSrc = props.pawnBuff ? props.type + `${props.pawnBuff + 1}` : props.type
    const image_src = IMAGE_MAP[buffedSrc] ? buffedSrc : props.type

    return(
        <div>
            <img 
                src={IMAGE_MAP[image_src]} 
                alt={image_src} 
                className={pickClassName()}
                style={{
                    top: `${topPosition}vw`,
                    left: `${leftPosition}vw`
                }}
                onClick={() => handlePieceClick()}
            />
            {props.health ?
                <div style={{
                    position: 'absolute',
                    display: 'flex',
                    alignItems: 'center',
                    top: `${topPosition + (3.25 * (isMobile ? 2: 1))}vw`,
                    left: `${leftPosition + (0.15 * (isMobile ? 2: 1))}vw`
                }}>
                    <progress
                        className={pickClassName()}
                        value={props.health}
                        max={MAX_BOSS_HEALTH[pickClassName().replace("_piece", "")]}
                        style={{position: 'static', width: `${isMobile ? 5 : 2.5}vw`}}
                    />
                    <span className="hp-label" style={{fontSize: `${isMobile ? 1.8 : 0.9}vw`}}>
                        {props.health}/{MAX_BOSS_HEALTH[pickClassName().replace("_piece", "")]}
                    </span>
                </div> : null}
            {props.isStunned ?
                <img
                    src={IMAGE_MAP['stunned']}
                    alt='stunned'
                    className={pickClassName()}
                    style={{
                        top: `${topPosition}vw`,
                        left: `${leftPosition - (0.3 * (isMobile ? 2: 1))}vw`,
                        width: isMobile ? '5vw': '2.5vw'
                    }}
                    onClick={() => handlePieceClick()}
                /> : null}
            {props.energizeStacks || props.energizeStacks === 0 ? 
                <p 
                    className={pickClassName()}
                    style={{
                        top: `${topPosition + (2.55 * (isMobile ? 2: 1))}vw`,
                        left: `${leftPosition - (0.75 * (isMobile ? 2: 1))}vw`,
                        fontWeight: 'bold',
                        background: '-webkit-linear-gradient(white, blue)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        fontSize: isMobile ? '2.4vw': '1.2vw'
                    }}
                >
                    {props.energizeStacks}
                </p> : null
            }
            {props.bishopDebuff ?
                Array.from({length: props.bishopDebuff}, (_, i) => i + 1).map((count) => {
                    return(
                    <img 
                        src={IMAGE_MAP['bishopDebuff']}
                        className={pickClassName()}
                        style={{
                            width: isMobile ? '1.4vw': '0.7vw',
                            height: isMobile ? '1.4vw': '0.7vw',
                            top: `${topPosition + (isMobile ? 5.5 : 2.75)}vw`,
                            left: `${leftPosition - (isMobile ? 3 : 1.5) + (count * (isMobile ? 2 : 1))}vw`
                        }}
                    />);
                }): null
            }
            {
                props.bishopDebuff === 3 && props.side === PLAYERS[1] ?
                <div>
                    <button
                        style={{
                            ...pieceActionBtnStyle(-(isMobile ? 2.5 : 1.25), 0, '#63bbf2', '#24a0ed'),
                            fontSize: `${isMobile ? 1 : 0.5}vw`,
                            width: `${3.7 * (isMobile ? 2 : 1)}vw`,
                            boxSizing: 'border-box',
                            zIndex: 10
                        }}
                        onClick={() => handleCaptureButtonClick()}
                    >Capture</button>
                    <button
                        style={{
                            ...pieceActionBtnStyle(0, 0, '#ff4040', '#fd0e35'),
                            fontSize: `${isMobile ? 1 : 0.5}vw`,
                            width: `${3.7 * (isMobile ? 2 : 1)}vw`,
                            boxSizing: 'border-box',
                            zIndex: 10
                        }}
                        onClick={() => handleSpareButtonClick()}
                    >Spare</button>
                </div>
                : null
            }
            {
                props.markedForDeath && props.side === PLAYERS[0] ?
                <button
                    style={{
                        ...pieceActionBtnStyle(-(isMobile ? 1.5 : 0.75), 0, '#ff4040', '#fd0e35'),
                        fontSize: `${isMobile ? 1 : 0.5}vw`,
                        whiteSpace: 'normal',
                        padding: `${0.1 * (isMobile ? 2 : 1)}vw ${0.1 * (isMobile ? 2 : 1)}vw`,
                        width: `${3.7 * (isMobile ? 2 : 1)}vw`,
                        boxSizing: 'border-box',
                        zIndex: 10
                    }}
                    onClick={() => handleSurrenderButtonClick()}
                >Surrender Piece</button>
                : null
            }
            {
                props.castleMoves?.length > 0 ?
                <div>
                    {props.castleMoves.map((move) => {
                        const isQueenside = move[1] === 2
                        return (
                            <button
                                key={`castle-${move[1]}`}
                                style={{
                                    ...pieceActionBtnStyle(
                                        -(isMobile ? 2.5 : 1.25),
                                        isQueenside ? -(isMobile ? 8 : 4) : (isMobile ? 5.5 : 2.75),
                                        '#63bbf2', '#24a0ed'
                                    ),
                                    fontSize: `${isMobile ? 1.4 : 0.7}vw`,
                                }}
                                onClick={() => handleCastleButtonClick(move)}
                            >{isQueenside ? "Castle Left" : "Castle Right"}</button>
                        )
                    })}
                </div>
                : null
            }
            {props.checkProtection ?
                Array.from({length: props.checkProtection}, (_, i) => i + 1).map((count) => {
                    return(
                    <img 
                        src={IMAGE_MAP['checkProtection']}
                        className={pickClassName()}
                        style={{
                            width: isMobile ? '2.3vw': '1.15vw',
                            height: isMobile ? '2.3vw': '1.15vw',
                            top: `${topPosition}vw`,
                            left: `${leftPosition - (isMobile ? 3.5: 1.75) + (count * (isMobile ? 3.6: 1.2))}vw`
                        }}
                    />);
                }): null
            }
        </div>
    );
}

export default Piece;