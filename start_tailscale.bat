@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Modo TAILSCALE

echo.
echo ========================================================================
echo 🌐 BIBLIOTECA INTELIGENTE - MODO TAILSCALE
echo ========================================================================
echo 🔒 Acceso móvil seguro desde internet
echo 🌐 Frontend: http://100.81.201.68:3000
echo 🔧 Backend: https://100.81.201.68:8001
echo ========================================================================
echo.

REM Configurar variables de entorno para modo TAILSCALE
set MODE=TAILSCALE
set HOST=100.81.201.68
set PORT=8001
set USE_SSL=true
set FRONTEND_HOST=100.81.201.68
set FRONTEND_PORT=3000
set ALLOWED_ORIGINS=http://100.81.201.68:3000,https://100.81.201.68:3000,http://localhost:3000,https://localhost:3000
REM BOOKS_PATH se lee desde .env

echo 🔧 Configurando modo TAILSCALE...
echo   Frontend: http://100.81.201.68:3000
echo   Backend: https://100.81.201.68:8001
echo   SSL: Habilitado
echo   Acceso móvil: Habilitado
echo.

REM Verificar Tailscale
echo 🔍 Verificando Tailscale...
"C:\Program Files\Tailscale\tailscale.exe" status | findstr /C:"100.81.201.68" >nul
if errorlevel 1 (
    echo ⚠️  Tailscale no está conectado o la IP ha cambiado
    echo 💡 Abre la aplicación de Tailscale y asegúrate de que esté conectado
    pause
    exit /b 1
)
echo ✅ Tailscale conectado

echo 🚀 Iniciando servicios en modo TAILSCALE...
echo.

echo 📋 Se abrirán 2 ventanas:
echo    1. 🔧 Backend (Puerto 8001) - https://100.81.201.68:8001
echo    2. 🌐 Frontend (Puerto 3000) - http://100.81.201.68:3000
echo.
echo ✅ Funcionalidades disponibles:
echo    • Carga de archivos individuales
echo    • Carga de archivos ZIP
echo    • Acceso móvil seguro desde cualquier lugar
echo.
echo ⚠️  Limitaciones:
echo    • File System Access API no disponible (usar ZIP)
echo    • Requiere Tailscale en dispositivos móviles
echo.

pause

echo 🚀 Abriendo Backend TAILSCALE...
start "Backend TAILSCALE" cmd /k "cd backend && set HOST=100.81.201.68 && set PORT=8001 && set USE_SSL=true && set ALLOWED_ORIGINS=http://100.81.201.68:3000,https://100.81.201.68:3000,http://localhost:3000,https://localhost:3000 && python start_server.py"

timeout /t 5 /nobreak >nul

echo 🌐 Abriendo Frontend TAILSCALE...
start "Frontend TAILSCALE" cmd /k "cd frontend && npx serve -s build -l tcp://100.81.201.68:3000"

echo.
echo ✅ Servicios TAILSCALE iniciados
echo 🌐 Accede desde: http://100.81.201.68:3000
echo 📱 También accesible desde dispositivos móviles con Tailscale
echo.
pause
