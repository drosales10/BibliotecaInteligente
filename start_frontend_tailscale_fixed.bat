@echo off
chcp 65001 >nul
title Frontend Tailscale - Biblioteca Inteligente

echo.
echo ========================================================================
echo 🌐 BIBLIOTECA INTELIGENTE - FRONTEND TAILSCALE  
echo ========================================================================
echo 🌐 IP Tailscale: 100.81.201.68
echo 🔌 Puerto: 3000
echo ========================================================================
echo.

REM Ir al directorio del proyecto y luego al frontend
cd /d "%~dp0"
echo 📁 Directorio base: %CD%

cd frontend
echo 📁 Directorio frontend: %CD%
echo.

echo 🔍 Verificaciones...
echo ✅ Node.js disponible
echo ✅ npm disponible 
echo ✅ Directorio frontend encontrado

REM Verificar build
if not exist "build" (
    echo ❌ Directorio build no encontrado
    echo 💡 Ejecuta primero: npm run build
    pause
    exit /b 1
)
echo ✅ Directorio build encontrado

REM Verificar node_modules
if not exist "node_modules" (
    echo ❌ node_modules no encontrado
    echo 💡 Ejecuta primero: npm install
    pause
    exit /b 1
)
echo ✅ node_modules encontrado

echo.
echo 🚀 Iniciando servidor frontend...
echo 🌐 URL: http://100.81.201.68:3000
echo 📋 Los logs aparecerán a continuación...
echo ⏹️  Presiona Ctrl+C para detener
echo.
echo ----------------------------------------

REM Ejecutar el servidor
call npm run serve

echo.
echo ----------------------------------------
echo ⏹️  Servidor frontend detenido
pause
