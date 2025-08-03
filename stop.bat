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
