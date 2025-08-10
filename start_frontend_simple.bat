@echo off
chcp 65001 >nul
title Frontend Tailscale - Puerto 3000

echo.
echo ========================================================================
echo 🌐 FRONTEND TAILSCALE - BIBLIOTECA INTELIGENTE
echo ========================================================================
echo.

cd /d "%~dp0frontend"
echo 📁 Directorio: %CD%
echo.

echo 🚀 Iniciando servidor frontend...
echo 🌐 URL: http://100.81.201.68:3000
echo ⏹️  Presiona Ctrl+C para detener
echo.

npm run serve

echo.
echo ⏹️  Servidor detenido
pause
