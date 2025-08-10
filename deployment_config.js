/**
 * Configuración de Despliegue Múltiple para Biblioteca Inteligente
 * Soporta 3 modos: LOCAL, WIFI, TAILSCALE
 */

const deploymentModes = {
  LOCAL: {
    name: 'Local Development',
    description: 'Para desarrollo local con File System Access API',
    frontend: {
      host: 'localhost',
      port: 3000,
      protocol: 'http'
    },
    backend: {
      host: 'localhost', 
      port: 8001,
      protocol: 'http',
      ssl: false
    },
    features: {
      fileSystemAccess: true,
      mobileAccess: false,
      cors: ['http://localhost:3000', 'http://127.0.0.1:3000']
    }
  },
  
  WIFI: {
    name: 'WiFi Local Network',
    description: 'Para acceso desde dispositivos en la misma red WiFi',
    frontend: {
      host: '192.168.100.6',
      port: 3000,
      protocol: 'http'
    },
    backend: {
      host: '192.168.100.6',
      port: 8001, 
      protocol: 'http',
      ssl: false
    },
    features: {
      fileSystemAccess: false,
      mobileAccess: true,
      cors: [
        'http://192.168.100.6:3000',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
      ]
    }
  },
  
  TAILSCALE: {
    name: 'Tailscale Secure Network',
    description: 'Para acceso móvil seguro desde internet',
    frontend: {
      host: '100.81.201.68',
      port: 3000,
      protocol: 'http'
    },
    backend: {
      host: '100.81.201.68',
      port: 8001,
      protocol: 'https', 
      ssl: true
    },
    features: {
      fileSystemAccess: false,
      mobileAccess: true,
      cors: [
        'http://100.81.201.68:3000',
        'https://100.81.201.68:3000',
        'http://localhost:3000',
        'https://localhost:3000'
      ]
    }
  }
};

module.exports = deploymentModes;
