import React from 'react';
import { useState } from 'react';
import { GameStateContextData } from '../context/GameStateContext';
import { IMAGE_MAP } from '../utility';


const GeneralRules = (props) => {
    const [toggleDragonRules, setToggleDragonRules] = useState(false)
    const [toggleHeraldRules, setToggleHeraldRules] = useState(false)
    const [toggleNashorRules, setToggleNashorRules] = useState(false)
    
    const handleDragonRuleClick = () => {
        setToggleDragonRules(!toggleDragonRules)
        setToggleHeraldRules(false)
        setToggleNashorRules(false)
    }

    const handleHeraldRuleClick = () => {
        setToggleHeraldRules(!toggleHeraldRules)
        setToggleDragonRules(false)
        setToggleNashorRules(false)
    }

    const handleNashorRuleClick = () => {
        setToggleNashorRules(!toggleNashorRules)
        setToggleDragonRules(false)
        setToggleHeraldRules(false)
    }

    // for some reason margin auto doesn't work if we 
    // use a class and declare it in index.css
    const imageStyle = {
        height: props.isMobile ? "18.75vw": "9.375vw",
        display: "block", 
        margin: "auto"
    }

    return(
        <div>
            <h3>General</h3>
            <h4>File Control</h4>
            <p>Pieces moving down a file cannot move past the center unless they are already on the center. Squares in the center are marked with a darker color.</p>
            <img 
                src={IMAGE_MAP["centerOfBoard"]}
                style={imageStyle}
            />
            <h4>White Side Advantage</h4>
            <p>Black players now start the game with a pawn on d6 instead of d7.</p>
            <img 
                src={IMAGE_MAP["blackStart"]}
                style={imageStyle}
            />
            <h4>Neutral Objectives</h4>
            <p>These objectives take the form of neutral pieces that can be captured. This occurs by bringing a piece's hitpoint to 0. Moving a unit adjacent or on top of the neutral piece removes 1 hitpoint. However, pieces that spend more than 1 turn adjacent or on top of a neutral piece are immediately destroyed.</p>
            <div style={{display:"flex"}}>
                <img
                    src={IMAGE_MAP["neutralCombat1"]}
                    style={{...imageStyle, height: props.isMobile ? "23.4vw": "11.7vw"}}
                />
                <img
                    src={IMAGE_MAP["neutralCombat2"]}
                    style={{...imageStyle, height: props.isMobile ? "23.4vw": "11.7vw"}}
                />
            </div>
            <p>If a neutral monster goes 3 turns without losing health, it is instantly healed to full health. Buffs granted by capturing neutral pieces are given to the player who reduces its health to 0.</p>
            <p>Click on each objective below for more information</p>
            <div style={{display:"flex"}}>
                <img 
                    src={IMAGE_MAP["neutralDragon"]}
                    style={imageStyle}
                    onClick={() => handleDragonRuleClick()}
                />
                <img 
                    src={IMAGE_MAP["neutralBoardHerald"]}
                    style={imageStyle}
                    onClick={() => handleHeraldRuleClick()}

                />
                <img 
                    src={IMAGE_MAP["neutralBaronNashor"]}
                    style={imageStyle}
                    onClick={() => handleNashorRuleClick()}

                />
            </div>
            {toggleDragonRules ? 
                <div style={{marginTop: "3vw"}}>
                    <ul>
                        <li>5 HP</li>
                        <li>Every 10 turns, the Dragon spawns on the h4 square. Capturing dragon grants a stacking buff.</li>
                        <li>Buffs</li>
                        <ul>
                            <li>1 stack - Pawns gain 1+ movement</li>
                            <li>2 stacks - All pieces deal +1 bonus damage to neutral pieces</li>
                            <li>3 stacks - Pieces ignore unit collision with ally pawns</li>
                            <li>4 stacks - Pieces ignore unit collision with ally units</li>
                            <li>5 stacks - Pieces can capture enemy units by occupying an adjacent square. Only 1 unit per turn can be captured still, and in cases where multiple units can be captured in this way, it is up to the opponent's choice which to lose. This buff lasts 3 turns.</li>
                        </ul>
                    </ul>
                </div>
            : null}
            {toggleHeraldRules ? 
                <div style={{marginTop: "3vw"}}>
                    <ul>
                        <li>5 HP</li>
                        <li>Board Herald spawns on the a5 square on turn 10 and turn 20. Grants a 4-turn buff only to the piece who captured it.</li>
                        <li>Buff</li>
                        <ul>
                            <li>Pawns adjacent to the piece can capture other pawns and pieces 1 square in front of them.</li>
                        </ul>
                    </ul>
                </div>
            : null}
            {toggleNashorRules ? 
                <div style={{marginTop: "3vw"}}>
                    <ul>
                        <li>10 HP</li>
                        <li>Baron Nashor spawns on the a5 square every 15 turns after the 20th turn. Grants a 4-turn buff to all pawns.</li>
                        <li>Buff</li>
                        <ul>
                            <li>All ally pawns can capture other pawns and pieces 1 square in front of them. Additionally they cannot be captured by other pawns. If enemy pawns currently are immune to your pawns, Baron buff negates this for the duration of the buff.</li>
                        </ul>
                    </ul>
                </div>
            : null}

        </div>
    );
}

export default GeneralRules;