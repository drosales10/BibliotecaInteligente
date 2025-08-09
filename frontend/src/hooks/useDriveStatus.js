import { useState, useEffect, useCallback, useRef } from 'react';
import { getBackendUrl, checkBackendHealth } from '../config/api';

// Configuración de persistencia
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos en milisegundos
const RETRY_DELAY = 5000; // 5 segundos
const MAX_RETRIES = 2; // Reducir reintentos

export const useDriveStatus = () => {
  const [driveStatus, setDriveStatus] = useState({
    status: 'checking',
    message: 'Verificando estado de Google Drive...',
    storageInfo: null,
    setupRequired: false
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Referencias para manejo de caché y reintentos
  const cacheRef = useRef(null);
  const lastCheckRef = useRef(0);
  const retryCountRef = useRef(0);
  const timeoutRef = useRef(null);

  const isCacheValid = useCallback(() => {
    if (!cacheRef.current || !lastCheckRef.current) return false;
    return Date.now() - lastCheckRef.current < CACHE_DURATION;
  }, []);

  const clearCache = useCallback(() => {
    cacheRef.current = null;
    lastCheckRef.current = 0;
    retryCountRef.current = 0;
  }, []);

  const checkDriveStatus = useCallback(async (forceRefresh = false) => {
    // Si no es un refresh forzado y el caché es válido, usar caché
    if (!forceRefresh && isCacheValid()) {
      setDriveStatus(cacheRef.current);
      setLoading(false);
      setError('');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // Verificar primero si el backend está disponible
      const backendAvailable = await checkBackendHealth();
      if (!backendAvailable) {
        throw new Error('Backend no disponible');
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 segundos timeout
      
      const response = await fetch(`${getBackendUrl()}/api/drive/status`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      const newStatus = {
        status: data.status,
        message: data.message,
        storageInfo: data.storage_info || null,
        setupRequired: data.setup_required || false,
        healthCheck: data.health_check || null,
        timestamp: Date.now()
      };
      
      // Actualizar caché
      cacheRef.current = newStatus;
      lastCheckRef.current = Date.now();
      retryCountRef.current = 0;
      
      setDriveStatus(newStatus);
      setError('');
      
    } catch (err) {
      // Manejar diferentes tipos de errores
      let errorMessage = 'Error de conexión al verificar Google Drive';
      let status = 'error';
      
      if (err.name === 'AbortError') {
        errorMessage = 'Timeout al verificar Google Drive';
        status = 'timeout';
      } else if (err.message.includes('Failed to fetch') || err.message.includes('Backend no disponible')) {
        errorMessage = 'No se pudo conectar con el servidor';
        status = 'connection_error';
      }
      
      setError(errorMessage);
      setDriveStatus({
        status,
        message: errorMessage,
        storageInfo: null,
        setupRequired: false,
        timestamp: Date.now()
      });
      
      // Reintentar automáticamente solo si no es el último intento y no es un error de conexión
      if (retryCountRef.current < MAX_RETRIES && status !== 'connection_error') {
        retryCountRef.current++;
        
        timeoutRef.current = setTimeout(() => {
          checkDriveStatus(forceRefresh);
        }, RETRY_DELAY * retryCountRef.current);
      }
    } finally {
      setLoading(false);
    }
  }, [isCacheValid]);

  const refreshStatus = useCallback(() => {
    clearCache();
    checkDriveStatus(true);
  }, [clearCache, checkDriveStatus]);

  const clearDriveCache = useCallback(async () => {
    try {
      const response = await fetch(`${getBackendUrl()}/api/drive/clear-cache`, {
        method: 'POST'
      });
      
      if (response.ok) {
        clearCache();
        await checkDriveStatus(true);
        return { success: true, message: 'Caché limpiado exitosamente' };
      } else {
        throw new Error('Error al limpiar caché del servidor');
      }
    } catch (err) {
      console.error('Error al limpiar caché:', err);
      return { success: false, message: 'Error al limpiar caché' };
    }
  }, [clearCache, checkDriveStatus]);

  const getHealthStatus = useCallback(async () => {
    try {
      const response = await fetch(`${getBackendUrl()}/api/drive/health`);
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error al obtener health status:', err);
      return { error: 'No se pudo obtener el estado de salud' };
    }
  }, []);

  useEffect(() => {
    checkDriveStatus();
    
    // Cleanup al desmontar
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [checkDriveStatus]);

  // Verificación periódica cada 5 minutos si el estado es ok
  useEffect(() => {
    if (driveStatus.status === 'ok') {
      const intervalId = setInterval(() => {
        checkDriveStatus();
      }, 5 * 60 * 1000); // 5 minutos
      
      return () => clearInterval(intervalId);
    }
  }, [driveStatus.status, checkDriveStatus]);

  return {
    driveStatus,
    loading,
    error,
    refreshStatus,
    clearDriveCache,
    getHealthStatus,
    isCacheValid: isCacheValid(),
    retryCount: retryCountRef.current
  };
}; 