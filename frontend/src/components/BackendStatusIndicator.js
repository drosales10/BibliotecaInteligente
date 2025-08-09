import React, { useState, useEffect } from 'react';
import { checkBackendHealth } from '../config/api';
import './BackendStatusIndicator.css';

const BackendStatusIndicator = () => {
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);
  const [isChecking, setIsChecking] = useState(false);

  const checkBackend = async () => {
    setIsChecking(true);
    try {
      const available = await checkBackendHealth();
      setIsBackendAvailable(available);
    } catch (error) {
      setIsBackendAvailable(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkBackend();
    
    // Verificar cada 30 segundos
    const interval = setInterval(checkBackend, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (isBackendAvailable) {
    return null; // No mostrar nada si el backend está disponible
  }

  return (
    <div className="backend-status-indicator">
      <div className="status-content">
        <div className="status-icon">⚠️</div>
        <div className="status-text">
          <div className="status-title">Servidor no disponible</div>
          <div className="status-description">
            El servidor backend no está ejecutándose. Por favor, inicie el servidor.
          </div>
        </div>
        <button 
          className="retry-button"
          onClick={checkBackend}
          disabled={isChecking}
        >
          {isChecking ? 'Verificando...' : 'Reintentar'}
        </button>
      </div>
    </div>
  );
};

export default BackendStatusIndicator;
