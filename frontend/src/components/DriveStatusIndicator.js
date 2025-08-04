import React from 'react';
import { useDriveStatus } from '../hooks/useDriveStatus';
import './DriveStatusIndicator.css';

const DriveStatusIndicator = () => {
  const { driveStatus, loading, refreshStatus } = useDriveStatus();

  const getStatusIcon = () => {
    switch (driveStatus.status) {
      case 'ok':
        return '☁️';
      case 'not_configured':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusClass = () => {
    switch (driveStatus.status) {
      case 'ok':
        return 'drive-status-ok';
      case 'not_configured':
        return 'drive-status-warning';
      case 'error':
        return 'drive-status-error';
      default:
        return 'drive-status-loading';
    }
  };

  const formatStorageSize = (bytes) => {
    if (!bytes) return '0 MB';
    const mb = bytes / (1024 * 1024);
    const gb = mb / 1024;
    if (gb >= 1) {
      return `${gb.toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  if (loading) {
    return (
      <div className="drive-status-indicator drive-status-loading">
        <span className="drive-icon">⏳</span>
        <span className="drive-text">Verificando Google Drive...</span>
      </div>
    );
  }

  return (
    <div className={`drive-status-indicator ${getStatusClass()}`}>
      <span className="drive-icon">{getStatusIcon()}</span>
      <div className="drive-info">
        <span className="drive-text">
          {driveStatus.status === 'ok' ? 'Google Drive' : driveStatus.message}
        </span>
        {driveStatus.storageInfo && (
          <span className="drive-storage">
            {formatStorageSize(driveStatus.storageInfo.total_size_bytes)}
          </span>
        )}
      </div>
      {driveStatus.setupRequired && (
        <button 
          className="drive-setup-btn"
          onClick={() => {
            alert('Para configurar Google Drive, sigue las instrucciones en la documentación del backend.');
          }}
        >
          Configurar
        </button>
      )}
      <button 
        className="drive-refresh-btn"
        onClick={refreshStatus}
        title="Actualizar estado"
      >
        🔄
      </button>
    </div>
  );
};

export default DriveStatusIndicator; 