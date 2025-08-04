@echo off
echo ========================================
echo Verificando estado del entorno virtual
echo ========================================
echo.

REM Verificar si Python está instalado
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo    Instala Python desde https://python.org
    goto :end
) else (
    echo ✅ Python detectado:
    python --version
)

echo.

REM Verificar si el entorno virtual existe
echo [2/5] Verificando entorno virtual...
if exist "venv" (
    echo ✅ Entorno virtual existe en: venv\
) else (
    echo ❌ Entorno virtual no existe
    echo    Ejecuta setup_environment.bat para crearlo
    goto :end
)

echo.

REM Verificar si el entorno virtual está activado
echo [3/5] Verificando activación del entorno virtual...
if defined VIRTUAL_ENV (
    echo ✅ Entorno virtual activado: %VIRTUAL_ENV%
) else (
    echo ⚠️  Entorno virtual no está activado
    echo    Para activarlo: venv\Scripts\activate.bat
)

echo.

REM Verificar dependencias del backend
echo [4/5] Verificando dependencias del backend...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy, alembic" >nul 2>&1
    if errorlevel 1 (
        echo ❌ Faltan dependencias del backend
        echo    Ejecuta: venv\Scripts\activate.bat && cd backend && pip install -r requirements.txt
    ) else (
        echo ✅ Dependencias del backend instaladas
    )
) else (
    echo ❌ No se puede verificar - entorno virtual no configurado correctamente
)

echo.

REM Verificar dependencias del frontend
echo [5/5] Verificando dependencias del frontend...
if exist "frontend\node_modules" (
    echo ✅ Dependencias del frontend instaladas
) else (
    echo ⚠️  Dependencias del frontend no instaladas
    echo    Ejecuta: cd frontend && npm install
)

echo.
echo ========================================
echo Resumen del estado:
echo ========================================

if exist "venv" (
    echo ✅ Entorno virtual: Configurado
) else (
    echo ❌ Entorno virtual: No configurado
)

if defined VIRTUAL_ENV (
    echo ✅ Activación: Activo
) else (
    echo ⚠️  Activación: Inactivo
)

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "import fastapi" >nul 2>&1
    if errorlevel 1 (
        echo ❌ Backend: Dependencias faltantes
    ) else (
        echo ✅ Backend: Listo
    )
) else (
    echo ❌ Backend: No configurado
)

if exist "frontend\node_modules" (
    echo ✅ Frontend: Listo
) else (
    echo ⚠️  Frontend: Dependencias faltantes
)

echo.
echo ========================================
echo Comandos útiles:
echo ========================================
echo Para activar: venv\Scripts\activate.bat
echo Para ejecutar: start.bat
echo Para detener: stop.bat
echo Para limpiar: clean_environment.bat
echo.

:end
pause 