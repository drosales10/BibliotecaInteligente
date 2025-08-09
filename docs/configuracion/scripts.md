# 🚀 Scripts de Inicio y Configuración

## 📋 Descripción General

El proyecto incluye varios scripts de inicio para facilitar el desarrollo y despliegue de la aplicación. Estos scripts automatizan tareas comunes y aseguran que el entorno esté configurado correctamente.

## 🔧 Variables de Entorno

### Configuración Automática

Todos los scripts cargan automáticamente las variables de entorno desde el archivo `.env` en la raíz del proyecto.

#### Variables Disponibles

| Variable | Descripción | Valor por Defecto | Ejemplo |
|----------|-------------|-------------------|---------|
| `HOST` | Host del servidor backend | `localhost` | `0.0.0.0` |
| `PORT` | Puerto del servidor backend | `8001` | `8001` |
| `FRONTEND_PORT` | Puerto del servidor frontend | `3000` | `3000` |
| `LOG_LEVEL` | Nivel de logging | `info` | `debug`, `info`, `warning`, `error` |
| `RELOAD` | Habilitar reload automático | `true` | `false` |
| `GEMINI_API_KEY` | Clave de API de Gemini | - | `"tu_clave_aqui"` |

#### Archivo .env de Ejemplo

```env
# Configuración de la API de Gemini
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"

# Configuración del servidor para producción
HOST="0.0.0.0"
PORT=8001

# Configuración del frontend (opcional)
FRONTEND_PORT=3000

# Configuración de logging (opcional)
LOG_LEVEL="info"

# Configuración de reload (opcional, solo para desarrollo)
RELOAD="false"
```

## 🔧 Scripts Disponibles

### 1. `start.bat` - Script Principal (Desarrollo)

**Ubicación**: Raíz del proyecto  
**Propósito**: Inicia tanto el backend como el frontend automáticamente para desarrollo

#### Características
- ✅ Carga variables de entorno desde `.env`
- ✅ Inicia backend y frontend simultáneamente
- ✅ Abre ventanas separadas para cada servidor
- ✅ Usa `localhost` como host por defecto
- ✅ Habilita reload automático
- ✅ Mensajes informativos del progreso

#### Uso
```bash
# Desde la raíz del proyecto
.\start.bat
```

### 2. `start_production.bat` - Script de Producción

**Ubicación**: Raíz del proyecto  
**Propósito**: Inicia la aplicación en modo producción

#### Características
- ✅ Carga variables de entorno desde `.env`
- ✅ Usa `0.0.0.0` como host por defecto (accesible desde cualquier IP)
- ✅ Ejecuta migraciones de la base de datos
- ✅ Inicia el backend sin reload automático
- ✅ Muestra la configuración utilizada
- ✅ Configuración optimizada para producción

#### Uso
```bash
# Desde la raíz del proyecto
.\start_production.bat
```

### 3. `start_backend.bat` - Script del Backend

**Ubicación**: `backend/`  
**Propósito**: Inicia solo el servidor backend con configuración completa

#### Características
- ✅ Carga variables de entorno desde `.env`
- ✅ Verifica la existencia de Python
- ✅ Ejecuta migraciones automáticamente
- ✅ Usa Python de Miniconda específicamente
- ✅ Manejo de errores con mensajes claros
- ✅ Pausa al final para ver logs

#### Uso
```bash
# Desde el directorio backend
.\start_backend.bat
```

### 4. `check_config.bat` - Verificador de Configuración

**Ubicación**: Raíz del proyecto  
**Propósito**: Verifica la configuración de variables de entorno

#### Características
- ✅ Verifica si existe el archivo `.env`
- ✅ Crea archivo `.env` desde `env.example` si no existe
- ✅ Muestra la configuración actual
- ✅ Calcula URLs de acceso
- ✅ Valida configuración requerida

#### Uso
```bash
# Desde la raíz del proyecto
.\check_config.bat
```

### 5. `stop.bat` - Script de Parada

**Ubicación**: Raíz del proyecto  
**Propósito**: Detiene todos los procesos del proyecto

#### Contenido del Script
```batch
@echo off
echo ========================================
echo   Deteniendo Servidores de la Libreria
echo ========================================

echo Deteniendo procesos de Python...
taskkill /f /im python.exe 2>nul
if %errorlevel% equ 0 (
    echo Procesos de Python detenidos correctamente.
) else (
    echo No se encontraron procesos de Python ejecutándose.
)

echo.
echo Deteniendo procesos de Node.js...
taskkill /f /im node.exe 2>nul
if %errorlevel% equ 0 (
    echo Procesos de Node.js detenidos correctamente.
) else (
    echo No se encontraron procesos de Node.js ejecutándose.
)

echo.
echo Todos los servidores han sido detenidos.
pause
```

#### Uso
```bash
# Desde la raíz del proyecto
.\stop.bat
```

## 🔄 Flujo de Uso Recomendado

### Desarrollo Diario
1. **Iniciar proyecto**: `.\start.bat`
2. **Desarrollo**: Trabajar en el código
3. **Detener proyecto**: `.\stop.bat`

### Desarrollo Backend Solo
1. **Iniciar backend**: `cd backend && .\start_backend.bat`
2. **Desarrollo**: Trabajar en el backend
3. **Detener**: `Ctrl+C` en la ventana del backend

### Desarrollo Frontend Solo
1. **Iniciar frontend**: `cd frontend && npm start`
2. **Desarrollo**: Trabajar en el frontend
3. **Detener**: `Ctrl+C` en la terminal

## ⚙️ Configuración de Scripts

### Personalización de Rutas

Si tu instalación de Miniconda está en una ubicación diferente, edita los scripts:

```batch
REM Cambiar esta línea en los scripts
set PYTHON_PATH=C:\Users\TU_USUARIO\miniconda3\python.exe
```

### Puertos Personalizados

Para cambiar los puertos, edita los scripts:

```batch
REM Backend (puerto 8001)
"%PYTHON_PATH%" -m uvicorn main:app --reload --port 8001

REM Frontend (puerto 3000)
npm start
```

## 🚨 Solución de Problemas

### Error: "No se encontró Python"
**Solución**: Verificar que Miniconda esté instalado en la ruta correcta

### Error: "react-scripts no se reconoce"
**Solución**: Ejecutar `npm install` en el directorio `frontend`

### Error: "Puerto ya en uso"
**Solución**: Usar `.\stop.bat` para detener procesos existentes

### Error: "Alembic no encontrado"
**Solución**: Instalar Alembic: `pip install alembic`

## 📊 Monitoreo de Scripts

### Verificar Estado de Servidores
```bash
# Verificar procesos Python
Get-Process python -ErrorAction SilentlyContinue

# Verificar procesos Node.js
Get-Process node -ErrorAction SilentlyContinue

# Verificar puertos
netstat -an | findstr ":8001\|:3000"
```

### Logs de Scripts
- Los scripts muestran mensajes informativos
- Los errores se muestran en la consola
- Los logs del servidor aparecen en las ventanas separadas

## 🔮 Mejoras Futuras

### Scripts Planificados
- **`install.bat`**: Instalación automática de dependencias
- **`test.bat`**: Ejecución de tests automatizados
- **`build.bat`**: Construcción para producción
- **`deploy.bat`**: Despliegue automatizado

### Características Futuras
- **Configuración interactiva**: Menús de selección
- **Logs estructurados**: Archivos de log separados
- **Monitoreo automático**: Verificación de salud de servicios
- **Backup automático**: Respaldo de base de datos

## 📝 Notas de Desarrollo

### Convenciones de Scripts
- Usar `@echo off` para scripts limpios
- Incluir mensajes informativos
- Manejar errores apropiadamente
- Usar rutas absolutas cuando sea necesario

### Compatibilidad
- **Windows**: Scripts .bat optimizados
- **Linux/macOS**: Scripts .sh equivalentes (futuro)
- **Docker**: Scripts de contenedor (futuro)

## 🔗 Enlaces Relacionados

- [Configuración del Entorno](./../instalacion/entorno.md)
- [Solución de Problemas](./../instalacion/troubleshooting.md)
- [Arquitectura del Sistema](./../arquitectura/README.md) 