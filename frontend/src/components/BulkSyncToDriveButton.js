import React, { useState } from 'react';
import { useAppMode } from '../contexts/AppModeContext';
import './BulkSyncToDriveButton.css';

// URL base del backend
const BACKEND_URL = 'http://localhost:8001';

const BulkSyncToDriveButton = ({ books, onSyncComplete }) => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const { isLocalMode } = useAppMode();

  // Filtrar libros que se pueden sincronizar (solo locales, no sincronizados)
  const syncableBooks = books.filter(book => 
    book.source === 'local' && !book.synced_to_drive
  );

  // Solo mostrar el botón si estamos en modo local y hay libros para sincronizar
  if (!isLocalMode || syncableBooks.length === 0) {
    return null;
  }

  const handleBulkSyncToDrive = async () => {
    // Mostrar confirmación antes de sincronizar
    const confirmSync = window.confirm(
      `¿Estás seguro de que quieres sincronizar ${syncableBooks.length} libro${syncableBooks.length > 1 ? 's' : ''} a Google Drive?\n\n` +
      '⚠️ ADVERTENCIA: Los archivos locales serán eliminados después de la sincronización.\n' +
      'Los libros permanecerán solo en la nube.'
    );
    
    if (!confirmSync) {
      return;
    }

    try {
      setIsSyncing(true);
      setSyncStatus('syncing');

      // Sincronizar todos los libros en paralelo
      const syncPromises = syncableBooks.map(book => 
        fetch(`${BACKEND_URL}/api/drive/sync-book`, {
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
        })
      );

      const responses = await Promise.all(syncPromises);
      const results = await Promise.all(responses.map(res => res.json()));

      // Contar éxitos y errores
      const successfulSyncs = results.filter(result => result.success);
      const failedSyncs = results.filter(result => !result.success);

      if (successfulSyncs.length > 0) {
        setSyncStatus('success');
        
        // Notificar al componente padre sobre los libros sincronizados exitosamente
        if (onSyncComplete) {
          successfulSyncs.forEach((result, index) => {
            const book = syncableBooks[index];
            onSyncComplete(book.id, result);
          });
        }
        
        // Mostrar mensaje de éxito
        setTimeout(() => {
          setSyncStatus(null);
        }, 3000);
      }

      if (failedSyncs.length > 0) {
        setSyncStatus('error');
        console.error('Errores en sincronización:', failedSyncs);
        
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
          <span className="sync-text">Sincronizando {syncableBooks.length} libro{syncableBooks.length > 1 ? 's' : ''}...</span>
        </>
      );
    }

    switch (syncStatus) {
      case 'success':
        return (
          <>
            <span className="sync-icon">✅</span>
            <span className="sync-text">¡Sincronizados!</span>
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
            <span className="sync-text">Sincronizar {syncableBooks.length} libro{syncableBooks.length > 1 ? 's' : ''}</span>
          </>
        );
    }
  };

  const getButtonClass = () => {
    const baseClass = 'bulk-sync-to-drive-btn';
    if (isSyncing) return `${baseClass} syncing`;
    if (syncStatus === 'success') return `${baseClass} success`;
    if (syncStatus === 'error') return `${baseClass} error`;
    return baseClass;
  };

  return (
    <button
      className={getButtonClass()}
      onClick={handleBulkSyncToDrive}
      disabled={isSyncing}
      title={`Sincronizar ${syncableBooks.length} libro${syncableBooks.length > 1 ? 's' : ''} a Google Drive`}
    >
      {getButtonContent()}
    </button>
  );
};

export default BulkSyncToDriveButton; 