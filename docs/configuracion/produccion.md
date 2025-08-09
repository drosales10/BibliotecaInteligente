# 🚀 Configuración para Producción

## 📋 Descripción

Esta guía explica cómo configurar la aplicación para producción usando variables de entorno.

## 🔧 Variables de Entorno

### Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto con la siguiente configuración:

```env
# Configuración de la API de Gemini
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"

# Configuración del servidor para producción
HOST="0.0.0.0"
PORT=8001

# Configuración del frontend (opcional)
FRONTEND_PORT=3000

# Configuración de la base de datos (opcional)
DATABASE_URL="sqlite:///./library.db"

# Configuración de logging (opcional)
LOG_LEVEL="info"

# Configuración de reload (opcional, solo para desarrollo)
RELOAD="false"
```

### Variables Disponibles

| Variable | Descripción | Valor por Defecto | Ejemplo |
|----------|-------------|-------------------|---------|
| `HOST` | Host del servidor backend | `localhost` | `0.0.0.0` |
| `PORT` | Puerto del servidor backend | `8001` | `8001` |
| `FRONTEND_PORT` | Puerto del servidor frontend | `3000` | `3000` |
| `LOG_LEVEL` | Nivel de logging | `info` | `debug`, `info`, `warning`, `error` |
| `RELOAD` | Habilitar reload automático | `true` | `false` |
| `GEMINI_API_KEY` | Clave de API de Gemini | - | `"tu_clave_aqui"` |
| `DATABASE_URL` | URL de la base de datos | `sqlite:///./library.db` | `sqlite:///./library.db` |

## 🚀 Scripts de Inicio

### 1. Script de Producción

Para iniciar la aplicación en modo producción:

```bash
start_production.bat
```

Este script:
- ✅ Carga las variables de entorno desde `.env`
- ✅ Usa `0.0.0.0` como host por defecto (accesible desde cualquier IP)
- ✅ Ejecuta migraciones de la base de datos
- ✅ Inicia el backend sin reload automático
- ✅ Muestra la configuración utilizada

### 2. Script de Desarrollo

Para desarrollo local:

```bash
start.bat
```

Este script:
- ✅ Carga las variables de entorno desde `.env`
- ✅ Usa `localhost` como host por defecto
- ✅ Habilita reload automático
- ✅ Inicia tanto backend como frontend

### 3. Script Solo Backend

Para iniciar solo el backend:

```bash
backend/start_backend.bat
```

## 🔒 Configuración de Seguridad

### Para Producción

1. **Host**: Usar `0.0.0.0` para permitir conexiones externas
2. **Puerto**: Usar un puerto no estándar (ej: `8001`, `8080`)
3. **Logging**: Usar `info` o `warning` para reducir logs
4. **Reload**: Deshabilitar reload automático (`RELOAD=false`)

### Para Desarrollo

1. **Host**: Usar `localhost` para restringir acceso local
2. **Puerto**: Usar puertos estándar o de desarrollo
3. **Logging**: Usar `debug` para más información
4. **Reload**: Habilitar reload automático (`RELOAD=true`)

## 🌐 Configuración de Red

### Acceso Externo

Para permitir acceso desde otras máquinas en la red:

```env
HOST="0.0.0.0"
PORT=8001
```

### Acceso Local

Para restringir acceso solo a la máquina local:

```env
HOST="localhost"
PORT=8001
```

### Firewall

Asegúrate de configurar el firewall para permitir conexiones en el puerto especificado:

```bash
# Windows (PowerShell como administrador)
New-NetFirewallRule -DisplayName "Biblioteca Inteligente" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
```

## 📊 Monitoreo

### Logs

Los logs se configuran según la variable `LOG_LEVEL`:

- `debug`: Información detallada para desarrollo
- `info`: Información general (recomendado para producción)
- `warning`: Solo advertencias y errores
- `error`: Solo errores

### Health Check

Verifica el estado del servidor:

```bash
curl http://localhost:8001/books/health-check
```

## 🔄 Migración desde Configuración Anterior

### Antes (Hardcoded)

```python
# backend/start_server.py
uvicorn.run(
    "main:app",
    host="localhost",
    port=8001,
    reload=True,
    log_level="info"
)
```

### Después (Variables de Entorno)

```python
# backend/start_server.py
host = os.getenv("HOST", "localhost")
port = int(os.getenv("PORT", 8001))
log_level = os.getenv("LOG_LEVEL", "info")
reload = os.getenv("RELOAD", "true").lower() == "true"

uvicorn.run(
    "main:app",
    host=host,
    port=port,
    reload=reload,
    log_level=log_level
)
```

## 🚨 Solución de Problemas

### Error: "AttributeError: module 'logging' has no attribute"

**Descripción del problema:**
```
AttributeError: module 'logging' has no attribute '"INFO"'. Did you mean: 'INFO'?
```

**Causa:**
- Las variables de entorno se cargan con comillas desde el archivo `.env`
- El código intenta usar el valor con comillas como atributo de logging
- Variables definidas después de ser usadas

**Solución:**
1. **Automática:** Los scripts ya incluyen limpieza automática de comillas
2. **Manual:** Asegúrate de que las variables en `.env` no tengan comillas innecesarias
3. **Código:** Reorganización del código para definir variables antes de usarlas

**Ejemplo correcto de `.env`:**
```env
# ✅ Correcto (sin comillas innecesarias)
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=info

# ❌ Incorrecto (con comillas innecesarias)
HOST="0.0.0.0"
PORT="8001"
LOG_LEVEL="info"
```

**Verificación:**
```bash
# Ejecutar script de verificación
python test_startup.py

# O usar el script de verificación de Windows
check_config.bat
```

### Error: "Puerto ya en uso"

```bash
# Verificar procesos en el puerto
netstat -ano | findstr :8001

# Terminar proceso
taskkill /PID <PID> /F
```

### Error: "No se puede acceder desde red externa"

1. Verificar que `HOST="0.0.0.0"` en `.env`
2. Verificar configuración del firewall
3. Verificar que el puerto esté abierto

### Error: "Archivo .env no encontrado"

1. Crear archivo `.env` en la raíz del proyecto
2. Copiar configuración desde `env.example`
3. Ajustar valores según necesidades

### Verificación de Configuración

Para verificar que la configuración esté correcta:

```bash
# Ejecutar script de verificación
python test_config.py

# O usar el script de verificación de Windows
check_config.bat
```

## 📝 Ejemplos de Configuración

### Desarrollo Local

```env
HOST="localhost"
PORT=8001
FRONTEND_PORT=3000
LOG_LEVEL="debug"
RELOAD="true"
```

### Producción Interna

```env
HOST="0.0.0.0"
PORT=8001
FRONTEND_PORT=3000
LOG_LEVEL="info"
RELOAD="false"
```

### Producción Externa

```env
HOST="0.0.0.0"
PORT=8080
FRONTEND_PORT=3000
LOG_LEVEL="warning"
RELOAD="false"
```

## 🔗 Enlaces Útiles

- [Documentación de FastAPI](https://fastapi.tiangolo.com/deployment/)
- [Variables de Entorno en Python](https://docs.python.org/3/library/os.html#os.getenv)
- [Configuración de Uvicorn](https://www.uvicorn.org/settings/)
