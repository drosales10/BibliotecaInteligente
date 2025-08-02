@echo off
echo ========================================
echo    Deteniendo Servidores de la Libreria
echo ========================================

echo.
echo Buscando y deteniendo el servidor del Frontend (en puerto 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo Cerrando proceso con PID %%a y sus subprocesos...
    taskkill /F /PID %%a /T
)

echo.
echo Buscando y deteniendo el servidor del Backend (en puerto 8001)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    echo Cerrando proceso con PID %%a y sus subprocesos...
    taskkill /F /PID %%a /T
)

echo.
echo Todos los procesos han sido detenidos.
pause
