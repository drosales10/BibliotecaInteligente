@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Modo WIFI

echo.
echo ========================================================================
echo 📶 BIBLIOTECA INTELIGENTE - MODO WIFI
echo ========================================================================
echo 🏠 Acceso desde dispositivos en la misma red WiFi
echo 🌐 Frontend: http://192.168.100.6:3000
echo 🔧 Backend: http://192.168.100.6:8001
echo ========================================================================
echo.

REM Configurar variables de entorno para modo WIFI
set MODE=WIFI
set HOST=192.168.100.6
set PORT=8001
set USE_SSL=false
set FRONTEND_HOST=192.168.100.6
set FRONTEND_PORT=3000
set ALLOWED_ORIGINS=http://192.168.100.6:3000,http://localhost:3000,http://127.0.0.1:3000

echo 🔧 Configurando modo WIFI...
echo   Frontend: http://192.168.100.6:3000
echo   Backend: http://192.168.100.6:8001
echo   SSL: Deshabilitado
echo   Acceso WiFi: Habilitado
echo.

echo 🚀 Iniciando servicios en modo WIFI...
echo.

echo 📋 Se abrirán 2 ventanas:
echo    1. 🔧 Backend (Puerto 8001) - http://192.168.100.6:8001
echo    2. 🌐 Frontend (Puerto 3000) - http://192.168.100.6:3000
echo.
echo ✅ Funcionalidades disponibles:
echo    • Carga de archivos individuales
echo    • Carga de archivos ZIP
echo    • Acceso desde dispositivos en la red WiFi
echo.
echo ⚠️  Limitaciones:
echo    • File System Access API no disponible (usar ZIP)
echo.

pause

echo 🚀 Abriendo Backend WIFI...
start "Backend WIFI" cmd /k "cd backend && set HOST=192.168.100.6 && set PORT=8001 && set USE_SSL=false && set ALLOWED_ORIGINS=http://192.168.100.6:3000,http://localhost:3000,http://127.0.0.1:3000 && python start_server.py"

timeout /t 3 /nobreak >nul

echo 🌐 Abriendo Frontend WIFI...
start "Frontend WIFI" cmd /k "cd frontend && npx serve -s build -l tcp://192.168.100.6:3000"

echo.
echo ✅ Servicios WIFI iniciados
echo 🌐 Accede desde: http://192.168.100.6:3000
echo 📱 También accesible desde dispositivos móviles en la misma WiFi
echo.
pause
