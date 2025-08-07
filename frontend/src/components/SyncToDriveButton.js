import React, { useState } from 'react';
import { useAppMode } from '../contexts/AppModeContext';
import './SyncToDriveButton.css';

const SyncToDriveButton = ({ book, onSyncComplete }) => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const { isLocalMode } = useAppMode();

  // Solo mostrar el botón si estamos en modo local y el libro no está sincronizado
  if (!isLocalMode || book.source === 'drive' || book.synced_to_drive) {
    return null;
  }

  const handleSyncToDrive = async () => {
    // Mostrar confirmación antes de sincronizar
    const confirmSync = window.confirm(
      '¿Estás seguro de que quieres sincronizar este libro a Google Drive?\n\n' +
      '⚠️ ADVERTENCIA: El archivo local será eliminado después de la sincronización.\n' +
      'El libro permanecerá solo en la nube.'
    );
    
    if (!confirmSync) {
      return;
    }

    try {
      setIsSyncing(true);
      setSyncStatus('syncing');

      // Llamar al endpoint de sincronización
      const response = await fetch('/api/drive/sync-book', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          book_id: book.id,
          title: book.title,
          author: book.author,
          category: book.category
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setSyncStatus('success');
        
        // Notificar al componente padre que la sincronización se completó
        if (onSyncComplete) {
          onSyncComplete(book.id, result);
        }
        
        // Mostrar mensaje de éxito
        setTimeout(() => {
          setSyncStatus(null);
        }, 3000);
      } else {
        const errorData = await response.json();
        setSyncStatus('error');
        console.error('Error al sincronizar:', errorData);
        
        setTimeout(() => {
          setSyncStatus(null);
        }, 3000);
      }
    } catch (error) {
      setSyncStatus('error');
      console.error('Error de conexión al sincronizar:', error);
      
      setTimeout(() => {
        setSyncStatus(null);
      }, 3000);
    } finally {
      setIsSyncing(false);
    }
  };

  const getButtonContent = () => {
    if (isSyncing) {
      return (
        <>
          <span className="sync-icon">⏳</span>
          <span className="sync-text">Sincronizando...</span>
        </>
      );
    }

    switch (syncStatus) {
      case 'success':
        return (
          <>
            <span className="sync-icon">✅</span>
            <span className="sync-text">¡Sincronizado!</span>
          </>
        );
      case 'error':
        return (
          <>
            <span className="sync-icon">❌</span>
            <span className="sync-text">Error</span>
          </>
        );
      default:
        return (
          <>
            <span className="sync-icon">☁️</span>
            <span className="sync-text">Sincronizar</span>
          </>
        );
    }
  };

  const getButtonClass = () => {
    const baseClass = 'sync-to-drive-btn';
    if (isSyncing) return `${baseClass} syncing`;
    if (syncStatus === 'success') return `${baseClass} success`;
    if (syncStatus === 'error') return `${baseClass} error`;
    return baseClass;
  };

  return (
    <button
      className={getButtonClass()}
      onClick={handleSyncToDrive}
      disabled={isSyncing}
      title="Sincronizar libro a Google Drive"
    >
      {getButtonContent()}
    </button>
  );
};

export default SyncToDriveButton; 