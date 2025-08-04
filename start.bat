@echo off
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

REM Iniciar el servidor del Backend en una nueva ventana
echo Iniciando Backend en http://localhost:8001 ...
START "Backend" cmd /c "call venv\Scripts\activate.bat && cd backend && python -m uvicorn main:app --reload --port 8001"

REM Iniciar el servidor del Frontend en una nueva ventana
echo Iniciando Frontend en http://localhost:3000 ...
START "Frontend" cmd /c "cd frontend && npm start"

echo.
echo Servidores iniciados en segundo plano.
echo Puedes cerrar esta ventana.
timeout /t 5 >nul
