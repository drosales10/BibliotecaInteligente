import React, { useState, useEffect } from 'react';
import { useAppMode } from '../contexts/AppModeContext';
import './ModeNotification.css';

const ModeNotification = () => {
  const { appMode, isLocalMode, isDriveMode } = useAppMode();
  const [showNotification, setShowNotification] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (appMode) {
      const modeMessages = {
        local: {
          title: '💾 Modo Local',
          message: 'Los libros se almacenan en tu computadora'
        },
        drive: {
          title: '☁️ Modo Google Drive',
          message: 'Los libros se almacenan en la nube'
        }
      };

      setMessage(modeMessages[appMode]);
      setShowNotification(true);

      const timer = setTimeout(() => {
        setShowNotification(false);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [appMode]);

  if (!showNotification) return null;

  return (
    <div className={`mode-notification ${appMode}`}>
      <div className="notification-content">
        <span className="notification-icon">
          {isLocalMode ? '💾' : '☁️'}
        </span>
        <div className="notification-text">
          <div className="notification-title">{message.title}</div>
          <div className="notification-description">{message.message}</div>
        </div>
        <button 
          className="notification-close"
          onClick={() => setShowNotification(false)}
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default ModeNotification; 