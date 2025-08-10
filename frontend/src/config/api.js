// Configuración de la API del backend
// Esta función detecta automáticamente la URL del backend según el contexto

export const getBackendUrl = () => {
  const envBase = (process.env.REACT_APP_API_BASE_URL || '').trim();
  if (envBase) {
    // Permitir override explícito desde entorno (producción)
    return envBase.replace(/\/+$/, '');
  }

  const { protocol, hostname, port } = window.location;

  console.log('🔍 Detectando modo de despliegue:', { hostname, port, protocol });

  // MODO LOCAL: localhost con desarrollo
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.log('🏠 Modo LOCAL detectado');
    return `http://localhost:8001`;
  }

  // MODO WIFI: Red local (192.168.x.x)
  if (hostname.startsWith('192.168.')) {
    console.log('📶 Modo WIFI detectado');
    return `http://${hostname}:8001`;
  }

  // MODO TAILSCALE: Red Tailscale (100.x.x.x)
  if (hostname.startsWith('100.')) {
    console.log('🌐 Modo TAILSCALE detectado');
    return `https://${hostname}:8001`;
  }

  // Detección por IP genérica
  const isIp = /^\d{1,3}(\.\d{1,3}){3}$/.test(hostname);
  if (isIp) {
    const scheme = protocol === 'https:' ? 'https' : 'http';
    console.log('🔍 Modo IP genérico detectado:', scheme);
    return `${scheme}://${hostname}:8001`;
  }

  // Por defecto: usar mismo origen
  console.log('🔧 Modo por defecto: mismo origen');
  return '';
};

// Función para verificar si el backend está disponible
export const checkBackendHealth = async () => {
  try {
    const backendUrl = getBackendUrl();
    const apiUrl = backendUrl ? `${backendUrl}/api/drive/status` : '/api/drive/status';
    
    console.log('🔍 Verificando backend en:', apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(5000) // 5 segundos timeout
    });
    
    console.log('🔍 Respuesta del backend:', response.status, response.statusText);
    
    if (!response.ok) {
      console.warn('⚠️ Backend respondió con estado:', response.status);
      return false;
    }
    
    const data = await response.json();
    console.log('✅ Backend funcionando correctamente:', data.status);
    return true;
  } catch (error) {
    console.error('❌ Error al verificar backend:', error);
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
  const scheme = window.location.protocol === 'https:' ? 'https' : 'http';
  return `${scheme}://${getLocalIP()}:8001`;
};
