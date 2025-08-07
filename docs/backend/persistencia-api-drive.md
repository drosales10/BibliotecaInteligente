# Persistencia de la API de Google Drive

## Resumen

Se han implementado mejoras significativas en la persistencia y robustez de la API de Google Drive para asegurar una experiencia de usuario más estable y confiable.

## Mejoras Implementadas

### 1. Sistema de Caché Inteligente

#### Backend (`google_drive_manager.py`)
- **Caché de información de almacenamiento**: 5 minutos de duración
- **Caché de carpetas de categorías**: Evita consultas repetidas
- **Invalidación automática**: Se limpia al subir/eliminar archivos
- **Thread-safe**: Uso de locks para operaciones concurrentes

```python
# Configuración de caché
CACHE_DURATION = 300  # 5 minutos
self.storage_cache = None
self.cache_timestamp = 0
self._lock = threading.Lock()
```

#### Frontend (`useDriveStatus.js`)
- **Caché local**: 5 minutos en el navegador
- **Reintentos automáticos**: Hasta 3 intentos con backoff exponencial
- **Verificación periódica**: Cada 2 minutos si el estado es correcto
- **Timeout configurable**: 10 segundos por defecto

### 2. Reconexión Automática

#### Decorador de Reintentos
```python
@retry_on_error(max_retries=3, delay=2)
def initialize_service(self):
    # Lógica de inicialización con reintentos automáticos
```

#### Verificación de Conexión
```python
def _ensure_service_connection(self):
    """Asegura que el servicio esté conectado, reintentando si es necesario"""
    if not self.service:
        logger.info("Servicio no inicializado, intentando reconectar...")
        self.initialize_service()
```

### 3. Health Check Robusto

#### Nuevo Endpoint `/api/drive/health`
```json
{
  "drive_health": {
    "status": "healthy",
    "message": "Conexión con Google Drive funcionando correctamente",
    "root_folder_id": "1O--MTmTGc8GZXLwMkhQQdQu_oTm3bJ9z",
    "test_successful": true
  },
  "timestamp": 1703123456.789,
  "cache_valid": true
}
```

#### Health Check en el Manager
```python
def health_check(self):
    """Verifica la salud de la conexión con Google Drive"""
    try:
        self._ensure_service_connection()
        # Operación simple de prueba
        test_query = f"'{self.root_folder_id}' in parents"
        results = self.service.files().list(q=test_query, pageSize=1).execute()
        return {"status": "healthy", "test_successful": True}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
```

### 4. Manejo Mejorado de Timeouts

#### Backend
- **Timeout de 8 segundos** para health check
- **Threading con timeout** para evitar bloqueos
- **Respuestas específicas** para diferentes tipos de timeout

#### Frontend
- **AbortController** para cancelar requests
- **Timeout de 10 segundos** configurable
- **Manejo específico** de errores de timeout

### 5. Nuevos Endpoints

#### `/api/drive/clear-cache` (POST)
Limpia el caché del servidor para forzar una actualización.

#### `/api/drive/health` (GET)
Endpoint específico para health check con información detallada.

### 6. Componente de UI Mejorado

#### DriveStatusIndicator
- **Información detallada** del estado de la conexión
- **Botones de acción** para refresh y limpiar caché
- **Indicadores visuales** para diferentes estados
- **Información de caché** y timestamps
- **Soporte para modo oscuro**

## Configuración

### Variables de Entorno
```bash
# Duración del caché (segundos)
CACHE_DURATION=300

# Número máximo de reintentos
MAX_RETRIES=3

# Delay entre reintentos (segundos)
RETRY_DELAY=2
```

### Timeouts
```python
# Backend timeouts
HEALTH_CHECK_TIMEOUT = 8  # segundos
STORAGE_INFO_TIMEOUT = 10  # segundos

# Frontend timeouts
REQUEST_TIMEOUT = 10000  # milisegundos
CACHE_DURATION = 300000  # milisegundos (5 minutos)
```

## Monitoreo y Debugging

### Logs del Backend
```python
logger.info("Información de almacenamiento actualizada y cacheada")
logger.warning(f"Intento {attempt + 1}/{max_retries} falló")
logger.error(f"Error al obtener información de almacenamiento: {e}")
```

### Logs del Frontend
```javascript
console.log(`Reintentando verificación de Drive (${retryCount}/3)...`);
console.log('Caché limpiado exitosamente');
console.error('Error al verificar estado de Google Drive:', err);
```

### Script de Pruebas
```bash
python test_drive_persistence.py
```

## Beneficios

### 1. Rendimiento
- **Reducción de llamadas** a la API de Google Drive
- **Respuestas más rápidas** gracias al caché
- **Menor latencia** en operaciones repetidas

### 2. Estabilidad
- **Reconexión automática** en caso de fallos
- **Manejo robusto** de timeouts y errores
- **Recuperación automática** de estados de error

### 3. Experiencia de Usuario
- **Indicadores visuales** claros del estado
- **Acciones manuales** disponibles (refresh, limpiar caché)
- **Información detallada** sobre la conexión

### 4. Mantenibilidad
- **Código modular** y reutilizable
- **Logs detallados** para debugging
- **Configuración centralizada** de timeouts y reintentos

## Troubleshooting

### Problemas Comunes

#### 1. Timeout en Health Check
```json
{
  "status": "timeout",
  "message": "Timeout al verificar Google Drive - la operación tardó demasiado"
}
```
**Solución**: Verificar conectividad de red y credenciales de Google Drive.

#### 2. Caché Expirado
```json
{
  "cache_valid": false,
  "timestamp": 1703123456.789
}
```
**Solución**: Usar el botón "Limpiar caché" o esperar la actualización automática.

#### 3. Reintentos Fallidos
```javascript
console.log("Reintentando verificación de Drive (3/3)...");
```
**Solución**: Verificar que el backend esté funcionando y las credenciales sean válidas.

### Comandos de Debugging

#### Verificar Estado del Backend
```bash
curl -s http://localhost:8001/api/drive/status
```

#### Health Check Detallado
```bash
curl -s http://localhost:8001/api/drive/health
```

#### Limpiar Caché
```bash
curl -X POST http://localhost:8001/api/drive/clear-cache
```

#### Ejecutar Pruebas Completas
```bash
cd backend
python test_drive_persistence.py
```

## Próximas Mejoras

1. **Métricas de rendimiento** en tiempo real
2. **Alertas automáticas** para fallos críticos
3. **Configuración dinámica** de timeouts
4. **Sincronización bidireccional** mejorada
5. **Backup automático** de credenciales 