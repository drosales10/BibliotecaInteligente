import React, { useState } from 'react';
import './DriveStatusModal.css';

const DriveStatusModal = ({ driveStatus, loading, error, refreshStatus, clearDriveCache, isCacheValid, retryCount }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getStatusIcon = () => {
    if (loading) return '🔄';
    switch (driveStatus.status) {
      case 'ok':
        return '✅';
      case 'error':
      case 'connection_error':
        return '❌';
      case 'timeout':
        return '⏰';
      case 'not_configured':
        return '⚙️';
      case 'partial':
        return '⚠️';
      default:
        return '❓';
    }
  };

  const getStatusColor = () => {
    switch (driveStatus.status) {
      case 'ok':
        return 'status-ok';
      case 'error':
      case 'connection_error':
        return 'status-error';
      case 'timeout':
        return 'status-timeout';
      case 'not_configured':
        return 'status-warning';
      case 'partial':
        return 'status-partial';
      default:
        return 'status-unknown';
    }
  };

  const getStatusText = () => {
    if (loading) return 'Verificando conexión...';
    return driveStatus.message || 'Estado desconocido';
  };

  const formatStorageInfo = (storageInfo) => {
    if (!storageInfo) return null;
    
    const { total_size_mb, total_size_gb, root_folder_name } = storageInfo;
    return (
      <div className="storage-info">
        <div className="storage-item">
          <span className="storage-label">Carpeta:</span>
          <span className="storage-value">{root_folder_name}</span>
        </div>
        <div className="storage-item">
          <span className="storage-label">Tamaño:</span>
          <span className="storage-value">
            {total_size_mb > 1024 ? `${total_size_gb} GB` : `${total_size_mb} MB`}
          </span>
        </div>
      </div>
    );
  };

  const formatHealthCheck = (healthCheck) => {
    if (!healthCheck) return null;
    
    return (
      <div className="health-info">
        <div className="health-item">
          <span className="health-label">Estado:</span>
          <span className={`health-value ${healthCheck.status === 'healthy' ? 'healthy' : 'unhealthy'}`}>
            {healthCheck.status === 'healthy' ? 'Saludable' : 'Problema'}
          </span>
        </div>
        {healthCheck.test_successful !== undefined && (
          <div className="health-item">
            <span className="health-label">Prueba:</span>
            <span className={`health-value ${healthCheck.test_successful ? 'success' : 'failed'}`}>
              {healthCheck.test_successful ? 'Exitosa' : 'Fallida'}
            </span>
          </div>
        )}
      </div>
    );
  };

  const handleRefresh = () => {
    refreshStatus();
  };

  const handleClearCache = async () => {
    const result = await clearDriveCache();
    if (result.success) {
      console.log('Caché limpiado exitosamente');
    } else {
      console.error('Error al limpiar caché:', result.message);
    }
  };

  const toggleModal = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Botón de activación */}
      <button 
        className={`drive-status-trigger ${getStatusColor()}`}
        onClick={toggleModal}
        title="Ver estado de Google Drive"
      >
        <span className="trigger-icon">{getStatusIcon()}</span>
        <span className="trigger-text">Drive</span>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="drive-status-modal-overlay" onClick={toggleModal}>
          <div className="drive-status-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Estado de Google Drive</h3>
              <button className="modal-close" onClick={toggleModal}>
                ✕
              </button>
            </div>

            <div className={`modal-content ${getStatusColor()}`}>
              <div className="status-header">
                <span className="status-icon">{getStatusIcon()}</span>
                <span className="status-text">{getStatusText()}</span>
              </div>
              
              {error && (
                <div className="error-message">
                  <span className="error-icon">⚠️</span>
                  <span className="error-text">{error}</span>
                  {retryCount > 0 && (
                    <span className="retry-info">
                      (Reintento {retryCount}/3)
                    </span>
                  )}
                </div>
              )}
              
              {driveStatus.storageInfo && (
                <div className="status-details">
                  {formatStorageInfo(driveStatus.storageInfo)}
                </div>
              )}
              
              {driveStatus.healthCheck && (
                <div className="status-details">
                  {formatHealthCheck(driveStatus.healthCheck)}
                </div>
              )}
              
              <div className="cache-info">
                <span className="cache-label">Caché:</span>
                <span className={`cache-status ${isCacheValid ? 'valid' : 'invalid'}`}>
                  {isCacheValid ? 'Válido' : 'Expirado'}
                </span>
                {driveStatus.timestamp && (
                  <span className="cache-timestamp">
                    ({new Date(driveStatus.timestamp).toLocaleTimeString()})
                  </span>
                )}
              </div>
              
              {loading && (
                <div className="loading-indicator">
                  <div className="loading-spinner"></div>
                  <span>Verificando conexión...</span>
                </div>
              )}
            </div>

            <div className="modal-actions">
              <button 
                onClick={handleRefresh} 
                disabled={loading}
                className="action-button refresh-button"
              >
                🔄 Actualizar
              </button>
              <button 
                onClick={handleClearCache} 
                disabled={loading}
                className="action-button clear-cache-button"
              >
                🗑️ Limpiar Caché
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DriveStatusModal; 