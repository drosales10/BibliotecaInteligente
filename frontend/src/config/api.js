// Configuración de la API del backend
// Esta función detecta automáticamente la URL del backend según el contexto

export const getBackendUrl = () => {
  const currentHost = window.location.hostname;
  
  // Si accedemos desde localhost, usar localhost para el backend
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    return 'http://localhost:8001';
  }
  
  // Si accedemos desde la IP local de la computadora, usar esa IP
  if (currentHost === '192.168.100.6') {
    return 'http://192.168.100.6:8001';
  }
  
  // Para dispositivos móviles en la misma red, usar la IP local de la computadora
  return 'http://192.168.100.6:8001';
};

// Función para verificar si el backend está disponible
export const checkBackendHealth = async () => {
  try {
    const response = await fetch(`${getBackendUrl()}/api/drive/status`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000) // 5 segundos timeout
    });
    return response.ok;
  } catch (error) {
    console.error('Error al verificar backend:', error);
    return false;
  }
};

// URL base del backend (se actualiza automáticamente)
export const BACKEND_URL = getBackendUrl();

// Función para obtener la IP local de la computadora
export const getLocalIP = () => {
  return '192.168.100.6';
};

// Función para verificar si estamos en un dispositivo móvil
export const isMobileDevice = () => {
  const currentHost = window.location.hostname;
  return currentHost !== 'localhost' && currentHost !== '127.0.0.1' && currentHost !== '192.168.100.6';
};

// Función para obtener la URL del backend para dispositivos móviles
export const getMobileBackendUrl = () => {
  return `http://${getLocalIP()}:8001`;
};
