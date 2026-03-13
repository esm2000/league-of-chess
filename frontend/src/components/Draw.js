import React from 'react';
import { IMAGE_MAP } from '../utility';

const Draw = (props) => {

    const topPosition = props.isMobile ? 22 : 11
    const leftPosition = props.isMobile ? 13 : 6.5
    const height = props.isMobile ? 13 : 6.5

    return(
        <div>
            <img
                src={IMAGE_MAP["draw"]}
                style={
                    {
                        position: "absolute",
                        top: `${topPosition}vw`,
                        left: `${leftPosition}vw`,
                        height: `${height}vw`
                    }}
            />
        </div>
    );
}

export default Draw;
