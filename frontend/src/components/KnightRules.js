import React from 'react';
import { GameStateContextData } from '../context/GameStateContext';
import { IMAGE_MAP } from '../utility';


const KnightRules = (props) => {
    const gameState = GameStateContextData()

    const imageStyle = {
        height: props.isMobile ? "25.3vw": "12.65vw",
        display: "block", 
        margin: "auto"
    }

    return(
        <div>
            <h3>Knights</h3>
            <p>Move in a L-shape, 2 squares in one direction, 1 square perpendicular to the direction chosen.</p>
            <img
                src={IMAGE_MAP["knightMovement"]}
                style={imageStyle}
            />
            <p style={{fontWeight: "bold"}}>CANNOT JUMP OVER OTHER PIECES</p>
            <img
                src={IMAGE_MAP["knightLimits"]}
                style={imageStyle}
            />
        </div>
    );
}

export default KnightRules;