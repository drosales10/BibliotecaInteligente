@echo off
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

REM Iniciar el servidor
echo.
echo Iniciando el servidor backend en http://localhost:8001
echo Presiona Ctrl+C para detener el servidor
echo.
python -m uvicorn main:app --reload --port 8001

pause 