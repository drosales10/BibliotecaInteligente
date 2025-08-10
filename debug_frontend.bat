@echo off
chcp 65001 >nul
title DEBUG - Frontend Tailscale

echo ========== DEBUG FRONTEND ==========
echo.

echo [1] Directorio inicial: %CD%
cd /d "%~dp0"
echo [2] Después de cd: %CD%

echo [3] Verificando Node.js...
node --version
echo [4] Node.js OK

echo [5] Verificando npm...
npm --version  
echo [6] npm OK

echo [7] Cambiando a directorio frontend...
cd frontend
echo [8] Directorio frontend: %CD%

echo [9] Verificando si existe build...
if exist "build" (
    echo [10] Build existe
) else (
    echo [10] Build NO existe
)

echo [11] Verificando si existe node_modules...
if exist "node_modules" (
    echo [12] node_modules existe  
) else (
    echo [12] node_modules NO existe
)

echo [13] Verificando package.json...
if exist "package.json" (
    echo [14] package.json existe
) else (
    echo [14] package.json NO existe
)

echo [15] A punto de ejecutar npm run serve...
echo [16] Ejecutando...

npm run serve

echo [17] npm run serve terminó
echo [18] Código de salida: %errorlevel%

pause
