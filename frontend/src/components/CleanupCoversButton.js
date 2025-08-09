import React, { useState } from 'react';
import { getBackendUrl } from '../config/api';
import './CleanupCoversButton.css';

const CleanupCoversButton = ({ onCleanupComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleCleanup = async () => {
    if (!window.confirm('¿Estás seguro de que quieres limpiar las portadas huérfanas? Esta acción no se puede deshacer.')) {
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${getBackendUrl()}/api/covers/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Error al limpiar portadas');
      }

      const result = await response.json();
      setMessage(`✅ ${result.message}`);
      
      if (onCleanupComplete) {
        onCleanupComplete(result);
      }

      setTimeout(() => {
        setMessage('');
      }, 5000);
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="cleanup-covers-container">
      <button
        onClick={handleCleanup}
        disabled={isLoading}
        className="cleanup-covers-button"
        title="Limpiar portadas huérfanas"
      >
        {isLoading ? '🧹 Limpiando...' : '🧹 Limpiar Portadas'}
      </button>
      {message && (
        <div className={`cleanup-message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default CleanupCoversButton;
