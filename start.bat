@echo off
setlocal enabledelayedexpansion
echo ========================================
echo   Iniciando Servidores de la Libreria
echo ========================================

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

REM Obtener configuración desde variables de entorno o usar valores por defecto
if defined HOST (
    set SERVER_HOST=%HOST%
) else (
    set SERVER_HOST=localhost
)

if defined PORT (
    set SERVER_PORT=%PORT%
) else (
    set SERVER_PORT=8001
)

if defined FRONTEND_PORT (
    set FRONTEND_PORT_NUM=%FRONTEND_PORT%
) else (
    set FRONTEND_PORT_NUM=3000
)

REM Iniciar el servidor del Backend en una nueva ventana
echo Iniciando Backend en http://%SERVER_HOST%:%SERVER_PORT% ...
START "Backend" cmd /c "call venv\Scripts\activate.bat && cd backend && python -m uvicorn main:app --reload --host %SERVER_HOST% --port %SERVER_PORT%"

REM Iniciar el servidor del Frontend en una nueva ventana
echo Iniciando Frontend en http://localhost:%FRONTEND_PORT_NUM% ...
START "Frontend" cmd /c "cd frontend && npm start"

echo.
echo Servidores iniciados en segundo plano.
echo Puedes cerrar esta ventana.
timeout /t 5 >nul
