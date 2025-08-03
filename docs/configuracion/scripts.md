# 🚀 Scripts de Inicio y Configuración

## 📋 Descripción General

El proyecto incluye varios scripts de inicio para facilitar el desarrollo y despliegue de la aplicación. Estos scripts automatizan tareas comunes y aseguran que el entorno esté configurado correctamente.

## 🔧 Scripts Disponibles

### 1. `start.bat` - Script Principal

**Ubicación**: Raíz del proyecto  
**Propósito**: Inicia tanto el backend como el frontend automáticamente

#### Contenido del Script
```batch
@echo off
echo ========================================
echo   Iniciando Servidores de la Libreria
echo ========================================

REM Iniciar el servidor del Backend en una nueva ventana
echo Iniciando Backend en http://localhost:8001 ...
START "Backend" cmd /c "cd backend && "C:\Users\Javier Rosales\miniconda3\python.exe" -m uvicorn main:app --reload --port 8001"

REM Iniciar el servidor del Frontend en una nueva ventana
echo Iniciando Frontend en http://localhost:3000 ...
START "Frontend" cmd /c "cd frontend && npm start"

echo.
echo Servidores iniciados en segundo plano.
echo Puedes cerrar esta ventana.
timeout /t 5 >nul
```

#### Uso
```bash
# Desde la raíz del proyecto
.\start.bat
```

#### Características
- ✅ Inicia backend y frontend simultáneamente
- ✅ Abre ventanas separadas para cada servidor
- ✅ Usa Python de Miniconda automáticamente
- ✅ Mensajes informativos del progreso

### 2. `start_backend.bat` - Script del Backend

**Ubicación**: `backend/`  
**Propósito**: Inicia solo el servidor backend con configuración completa

#### Contenido del Script
```batch
@echo off
echo Iniciando el backend de la Libreria Inteligente...
echo.

REM Configurar el Python de Miniconda
set PYTHON_PATH=C:\Users\Javier Rosales\miniconda3\python.exe

REM Verificar que Python existe
if not exist "%PYTHON_PATH%" (
    echo Error: No se encontró Python en %PYTHON_PATH%
    echo Por favor, verifica que Miniconda esté instalado correctamente.
    pause
    exit /b 1
)

echo Usando Python: %PYTHON_PATH%
echo.

REM Ejecutar las migraciones de la base de datos
echo Ejecutando migraciones de la base de datos...
"%PYTHON_PATH%" -m alembic upgrade head

REM Iniciar el servidor
echo.
echo Iniciando el servidor backend en http://localhost:8001
echo Presiona Ctrl+C para detener el servidor
echo.
"%PYTHON_PATH%" -m uvicorn main:app --reload --port 8001

pause
```

#### Uso
```bash
# Desde el directorio backend
.\start_backend.bat
```

#### Características
- ✅ Verifica la existencia de Python
- ✅ Ejecuta migraciones automáticamente
- ✅ Usa Python de Miniconda específicamente
- ✅ Manejo de errores con mensajes claros
- ✅ Pausa al final para ver logs

### 3. `stop.bat` - Script de Parada

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