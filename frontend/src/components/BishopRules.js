import React from 'react';
import { GameStateContextData } from '../context/GameStateContext';
import { IMAGE_MAP } from '../utility';


const BishopRules = (props) => {
    const gameState = GameStateContextData()

    const imageStyle = {
        height: props.isMobile ? "22vw": "11vw", 
        display: "block", 
        margin: "auto"
    }

    return(
        <div>
            <h3>Bishops</h3>
            <p>Move along diagonals</p>
            <img
                src={IMAGE_MAP["bishopMovement"]}
                style={imageStyle}
            />
            <p>Generate <span style={{color: "rgb(0, 239, 255)"}}>Energize</span> stacks by moving and capturing</p>
            <div style={{display: "flex"}}>
                <img
                    src={IMAGE_MAP["bishopStacksMovement"]}
                    style={imageStyle}
                />
                <img
                    src={IMAGE_MAP["bishopStacksCapture"]}
                    style={imageStyle}
                />
            </div>
            <p>At 100 stacks, the next capture action can now capture other pieces by landing on any square adjacently diagonal to opponent's piece</p>
            <img
                src={IMAGE_MAP["bishopEnergizedCapture"]}
                style={{...imageStyle, marginTop: props.isMobile ? "2vw": "1vw"}}
            />
            <p>Threatening to capture a piece applies a debuff at the end of a bishops's turn to that piece. On third hit of debuff, a bishop may immediately capture the enemy piece</p>
            <img
                src={IMAGE_MAP["bishopDebuffEx"]}
                style={imageStyle}
            />
            <p style={{fontWeight: "bold", color: "red"}}>Can be captured by landing on any square adjacent to it</p>
            <img
                src={IMAGE_MAP["bishopCapture"]}
                style={imageStyle}
            />
        </div>
    );
}

export default BishopRules;