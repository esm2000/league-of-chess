import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import "./fonts/Retro_Gaming.TTF";
import "./fonts/04B_30__.TTF"

import { GameStateProvider } from './context/GameStateContext';
import { CaptureApp, isCaptureModeEnabled } from './capture/CaptureApp';

import Board from './components/Board';
import Rules from './components/Rules';
import Title from './components/Title';


 
class App extends React.Component {
    constructor(props) {
        super(props);
    }
    
    render() {
        return (
            <div>
                <GameStateProvider>
                    <Title />
                    <div className='board-and-rules-container'>
                        <Board />
                        <Rules />
                    </div>
                </GameStateProvider>
            </div>
        );
    }
  }
  
  // ========================================
  
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(isCaptureModeEnabled() ? <CaptureApp /> : <App />);
  
  
