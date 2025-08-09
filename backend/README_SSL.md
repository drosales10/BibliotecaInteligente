# 🔒 Solución de Problemas SSL para Dispositivos Móviles

## Problema Identificado
Los errores `[SSL: WRONG_VERSION_NUMBER] wrong version number` indican que los dispositivos móviles están intentando hacer conexiones HTTPS a un servidor HTTP.

## Solución Implementada
Se ha implementado soporte completo para HTTPS en el backend con certificados SSL autofirmados.

## 📋 Pasos para Solucionar

### 1. Instalar OpenSSL
- Descarga OpenSSL desde: https://slproweb.com/products/Win32OpenSSL.html
- Instala la versión Win64 OpenSSL v3.x.x
- **IMPORTANTE**: Reinicia la terminal después de la instalación

### 2. Generar Certificados SSL
```bash
cd backend
python generate_ssl.py
```

### 3. Iniciar Servidor con SSL
```bash
# Opción 1: Script automático (recomendado)
start_ssl_backend.bat

# Opción 2: Manual
python start_server.py
```

## 🔧 Configuración

### Variables de Entorno (.env)
```env
HOST=0.0.0.0
PORT=8001
USE_SSL=true
LOG_LEVEL=info
RELOAD=true
```

### URLs de Acceso
- **HTTP**: http://192.168.100.6:8001
- **HTTPS**: https://192.168.100.6:8001 (recomendado para móviles)

## 📱 Acceso desde Dispositivos Móviles

### 1. Conectar al WiFi de la misma red
### 2. Abrir navegador y acceder a:
```
https://192.168.100.6:8001
```

### 3. Aceptar la advertencia de seguridad
- Los navegadores mostrarán una advertencia porque es un certificado autofirmado
- Hacer clic en "Avanzado" → "Continuar a 192.168.100.6 (no seguro)"
- Esto es normal en desarrollo

## 🚨 Solución de Problemas

### Error: "OpenSSL no está disponible"
```bash
# Verificar instalación
openssl version

# Si no funciona, agregar al PATH:
# C:\Program Files\OpenSSL-Win64\bin
```

### Error: "Puerto en uso"
```bash
# Verificar procesos en el puerto 8001
netstat -ano | findstr :8001

# Terminar proceso si es necesario
taskkill /PID <PID> /F
```

### Error: "Permisos insuficientes"
- Ejecutar PowerShell como administrador
- Ejecutar el script de firewall: `configure_firewall_mobile.ps1`

## 🔍 Verificación

### 1. Verificar certificados SSL
```
backend/ssl/
├── cert.pem    # Certificado público
└── key.pem     # Clave privada
```

### 2. Verificar servidor HTTPS
```bash
# El servidor debe mostrar:
🔒 Configuración SSL detectada
✅ Servidor iniciando con HTTPS
```

### 3. Probar conexión HTTPS
```bash
curl -k https://192.168.100.6:8001/api/drive/status
```

## 📚 Archivos de Configuración

- `ssl_config.py` - Configuración SSL del servidor
- `generate_ssl.py` - Generador de certificados
- `start_ssl_backend.bat` - Script de inicio con SSL
- `env.example` - Variables de entorno de ejemplo

## 🎯 Beneficios de HTTPS

- ✅ **Compatibilidad móvil**: Los dispositivos móviles modernos prefieren HTTPS
- ✅ **Seguridad**: Conexiones encriptadas
- ✅ **Confianza**: Los navegadores confían más en conexiones HTTPS
- ✅ **Funcionalidad**: Todas las características del navegador funcionan correctamente

## ⚠️ Notas Importantes

1. **Certificados autofirmados**: Solo para desarrollo, no para producción
2. **Advertencias de seguridad**: Normales en desarrollo con certificados autofirmados
3. **IP local**: Asegúrate de usar la IP correcta de tu red local
4. **Firewall**: Configura el firewall para permitir conexiones al puerto 8001

## 🆘 Soporte

Si persisten los problemas:
1. Verifica que OpenSSL esté instalado y en el PATH
2. Revisa los logs del servidor
3. Verifica la configuración del firewall
4. Asegúrate de que la IP sea accesible desde el dispositivo móvil
