@echo off
setlocal enabledelayedexpansion
echo Iniciando el backend de la Libreria Inteligente...
echo.

REM Verificar que Python existe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: No se encontró Python
    echo Por favor, verifica que Miniconda esté instalado correctamente.
    pause
    exit /b 1
)

echo Usando Python: 
python --version
echo.

REM Ejecutar las migraciones de la base de datos
echo Ejecutando migraciones de la base de datos...
python -m alembic upgrade head

REM Cargar variables de entorno si existe el archivo .env
if exist "..\.env" (
    echo Cargando configuración desde .env...
    for /f "tokens=1,2 delims==" %%a in (..\.env) do (
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

REM Iniciar el servidor
echo.
echo Iniciando el servidor backend en http://%SERVER_HOST%:%SERVER_PORT%
echo Presiona Ctrl+C para detener el servidor
echo.
python -m uvicorn main:app --reload --host %SERVER_HOST% --port %SERVER_PORT%

pause 