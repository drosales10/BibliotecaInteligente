@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Modo LOCAL

echo.
echo ========================================================================
echo 🏠 BIBLIOTECA INTELIGENTE - MODO LOCAL
echo ========================================================================
echo 💻 Desarrollo local con File System Access API
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:8001
echo ========================================================================
echo.

REM Configurar variables de entorno para modo LOCAL
set MODE=LOCAL
REM set HOST=localhost
REM set PORT=8001
REM set USE_SSL=false
REM set FRONTEND_HOST=localhost
REM set FRONTEND_PORT=3000
REM set ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
REM set BOOKS_PATH=E:\books

echo 🔧 Configurando modo LOCAL...
echo   Frontend: http://localhost:3000
echo   Backend: http://localhost:8001
echo   SSL: Deshabilitado
echo   File System Access: Habilitado
echo.

echo 🚀 Iniciando servicios en modo LOCAL...
echo.

echo 📋 Se abrirán 2 ventanas:
echo    1. 🔧 Backend (Puerto 8001) - http://localhost:8001
echo    2. 🌐 Frontend (Puerto 3000) - http://localhost:3000
echo.
echo ✅ Funcionalidades disponibles:
echo    • Carga de archivos individuales
echo    • Carga de carpetas (File System Access API)
echo    • Carga de archivos ZIP
echo    • Acceso solo desde localhost
echo.

pause

echo 🚀 Abriendo Backend LOCAL...
start "Backend LOCAL" cmd /k "cd backend && python start_server.py"

timeout /t 3 /nobreak >nul

echo 🌐 Abriendo Frontend LOCAL...
start "Frontend LOCAL" cmd /k "cd frontend && npx serve -s build -l tcp://localhost:3000"

echo.
echo ✅ Servicios LOCAL iniciados
echo 🌐 Accede desde: http://localhost:3000
echo.
pause
