import React, { useState, useEffect } from 'react';
import './ModeSelector.css';

const ModeSelector = ({ onModeChange, currentMode = 'local' }) => {
  const [mode, setMode] = useState(currentMode);

  useEffect(() => {
    const savedMode = localStorage.getItem('appMode') || 'local';
    setMode(savedMode);
    onModeChange(savedMode);
  }, [onModeChange]);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    localStorage.setItem('appMode', newMode);
    onModeChange(newMode);
  };

  return (
    <div className="mode-selector">
      <div className="mode-toggle">
        <button
          className={`mode-btn ${mode === 'local' ? 'active' : ''}`}
          onClick={() => handleModeChange('local')}
          title="Modo Local - Los libros se almacenan en tu computadora"
        >
          <span className="mode-icon">💾</span>
          <span className="mode-text">Local</span>
        </button>
        <button
          className={`mode-btn ${mode === 'drive' ? 'active' : ''}`}
          onClick={() => handleModeChange('drive')}
          title="Modo Google Drive - Los libros se almacenan en la nube"
        >
          <span className="mode-icon">☁️</span>
          <span className="mode-text">Drive</span>
        </button>
      </div>
      <div className="mode-indicator">
        <span className={`mode-badge ${mode}`}>
          {mode === 'local' ? '💾 Local' : '☁️ Drive'}
        </span>
      </div>
    </div>
  );
};

export default ModeSelector; 