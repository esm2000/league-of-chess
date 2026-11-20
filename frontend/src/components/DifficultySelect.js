import React from 'react';
import { CPU_DIFFICULTIES } from '../utility';

const LABELS = {
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard'
}

const getDifficultyLabel = (difficulty) => LABELS[difficulty] || LABELS.easy

// Row of Easy / Medium / Hard buttons. `selected` is only highlighted as the default;
// clicking any button calls onSelect with that difficulty.
const DifficultySelect = ({ selected, onSelect, buttonStyle }) => {
    return (
        <>
            {CPU_DIFFICULTIES.map(difficulty => (
                <button
                    key={difficulty}
                    className={`pixel-btn${difficulty === selected ? ' pixel-btn-selected' : ''}`}
                    onClick={() => onSelect(difficulty)}
                    style={buttonStyle}
                >{getDifficultyLabel(difficulty)}</button>
            ))}
        </>
    );
}

export { getDifficultyLabel }

export default DifficultySelect;
