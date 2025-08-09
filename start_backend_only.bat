@echo off
setlocal enabledelayedexpansion
echo ========================================
echo   Iniciando Solo el Backend
echo ========================================
echo.

REM Verificar si el entorno virtual existe
if not exist "venv" (
    echo ERROR: El entorno virtual no existe
    echo Ejecuta setup_environment.bat primero para configurar el entorno
    pause
    exit /b 1
)

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM Cargar variables de entorno si existe el archivo .env
if exist ".env" (
    echo Cargando configuración desde .env...
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            REM Limpiar comillas del valor
            set "temp_value=%%b"
            set "temp_value=!temp_value:"=!"
            set "temp_value=!temp_value:'=!"
            set "%%a=!temp_value!"
        )
    )
)

REM Establecer valores por defecto si no están definidos
if not defined HOST set HOST=localhost
if not defined PORT set PORT=8001
if not defined LOG_LEVEL set LOG_LEVEL=info
if not defined RELOAD set RELOAD=true

echo Configuración del servidor:
echo   Host: %HOST%
echo   Puerto: %PORT%
echo   Log Level: %LOG_LEVEL%
echo   Reload: %RELOAD%
echo.

REM Ejecutar las migraciones de la base de datos
echo Ejecutando migraciones de la base de datos...
cd backend
python -m alembic upgrade head
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron ejecutar las migraciones
    pause
    exit /b 1
)

REM Iniciar el servidor backend
echo.
echo Iniciando el servidor backend en http://%HOST%:%PORT%
echo Presiona Ctrl+C para detener el servidor
echo.
python -m uvicorn main:app --host %HOST% --port %PORT% --reload --log-level %LOG_LEVEL%

pause
