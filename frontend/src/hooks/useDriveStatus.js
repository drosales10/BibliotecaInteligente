import { useState, useEffect, useCallback } from 'react';

export const useDriveStatus = () => {
  const [driveStatus, setDriveStatus] = useState({
    status: 'checking',
    message: 'Verificando estado de Google Drive...',
    storageInfo: null,
    setupRequired: false
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const checkDriveStatus = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8001/drive/status');
      const data = await response.json();
      
      setDriveStatus({
        status: data.status,
        message: data.message,
        storageInfo: data.storage_info || null,
        setupRequired: data.setup_required || false
      });
    } catch (err) {
      console.error('Error al verificar estado de Google Drive:', err);
      setError('Error de conexión al verificar Google Drive');
      setDriveStatus({
        status: 'error',
        message: 'No se pudo conectar con el servidor',
        storageInfo: null,
        setupRequired: false
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshStatus = useCallback(() => {
    checkDriveStatus();
  }, [checkDriveStatus]);

  useEffect(() => {
    checkDriveStatus();
  }, [checkDriveStatus]);

  return {
    driveStatus,
    loading,
    error,
    refreshStatus
  };
}; 