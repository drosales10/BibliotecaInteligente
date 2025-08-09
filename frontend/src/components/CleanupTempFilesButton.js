import React, { useState } from 'react';
import { getBackendUrl } from '../config/api';
import './CleanupTempFilesButton.css';

const CleanupTempFilesButton = ({ onCleanupComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleCleanup = async () => {
    // Confirmación antes de proceder
    const confirmed = window.confirm(
      '¿Estás seguro de que quieres limpiar todos los archivos temporales?\n\n' +
      'Esta acción eliminará:\n' +
      '• Archivos de procesamiento temporal\n' +
      '• Archivos de carga masiva temporal\n' +
      '• Archivos de descarga temporal\n' +
      '• Archivos de libros temporales\n\n' +
      'Esta acción no se puede deshacer.'
    );

    if (!confirmed) return;

    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${getBackendUrl()}/api/cleanup-temp-files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al limpiar archivos temporales');
      }

      const result = await response.json();
      
      setMessage(`✅ ${result.message}`);
      
      // Notificar al componente padre
      if (onCleanupComplete) {
        onCleanupComplete(result);
      }

      // Limpiar mensaje después de 5 segundos
      setTimeout(() => {
        setMessage('');
      }, 5000);

    } catch (error) {
      console.error('Error limpiando archivos temporales:', error);
      setMessage(`❌ Error: ${error.message}`);
      
      // Limpiar mensaje de error después de 5 segundos
      setTimeout(() => {
        setMessage('');
      }, 5000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="cleanup-temp-files-container">
      <button
        className={`cleanup-temp-files-button ${isLoading ? 'loading' : ''}`}
        onClick={handleCleanup}
        disabled={isLoading}
        title="Limpiar archivos temporales"
      >
        {isLoading ? (
          <>
            <span className="cleanup-temp-files-icon">⏳</span>
            Limpiando...
          </>
        ) : (
          <>
            <span className="cleanup-temp-files-icon">🗑️</span>
            Purga de Archivos
          </>
        )}
      </button>
      
      {message && (
        <div className={`cleanup-temp-files-message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default CleanupTempFilesButton;
