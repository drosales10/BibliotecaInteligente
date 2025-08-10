@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Iniciador Tailscale

echo.
echo ================================================================================
echo 🌐 BIBLIOTECA INTELIGENTE - MODO TAILSCALE (VENTANAS SEPARADAS)
echo ================================================================================
echo 📱 Acceso seguro desde dispositivos móviles
echo 🔒 Conexión cifrada a través de red privada Tailscale
echo ================================================================================
echo.

REM Verificar configuración básica
echo 🔍 Verificando configuración...

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está disponible
    echo 💡 Instala Python desde https://python.org
    pause
    exit /b 1
)

REM Verificar si Node.js está disponible
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no está disponible
    echo 💡 Instala Node.js desde https://nodejs.org
    pause
    exit /b 1
)

REM Verificar si Tailscale está instalado
if not exist "C:\Program Files\Tailscale\tailscale.exe" (
    echo ❌ Tailscale no está instalado
    echo 💡 Instala Tailscale desde https://tailscale.com/download
    pause
    exit /b 1
)

echo ✅ Verificaciones completadas
echo.

REM Verificar estado de Tailscale
echo 🌐 Verificando conexión de Tailscale...
"C:\Program Files\Tailscale\tailscale.exe" status | findstr /C:"100.81.201.68" >nul
if errorlevel 1 (
    echo ⚠️  Tailscale no parece estar conectado o la IP ha cambiado
    echo 💡 Abre la aplicación de Tailscale y asegúrate de que esté conectado
    echo.
    echo ¿Deseas continuar de todas formas? (S/N)
    choice /C SN /M "Continuar"
    if errorlevel 2 (
        echo ❌ Operación cancelada
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Iniciando servicios en ventanas separadas...
echo.
echo 📋 Se abrirán 2 ventanas:
echo    1. 🔧 Backend (Puerto 8001) - https://100.81.201.68:8001
echo    2. 🌐 Frontend (Puerto 3000) - http://100.81.201.68:3000
echo.
echo ⚠️  IMPORTANTE:
echo    • Mantén ambas ventanas abiertas mientras uses la aplicación
echo    • Estas URLs solo funcionan en dispositivos conectados a Tailscale
echo    • Instala Tailscale en tu móvil con la misma cuenta para acceder
echo.

pause

echo 🚀 Abriendo Backend en nueva ventana...
start "Backend Tailscale" cmd /k "start_backend_tailscale.bat"

echo ⏳ Esperando 5 segundos para que el backend se inicie...
timeout /t 5 /nobreak >nul

echo 🌐 Abriendo Frontend en nueva ventana...
start "Frontend Tailscale" cmd /k "start_frontend_tailscale.bat"

echo.
echo ✅ Ambos servicios iniciándose...
echo.
echo 📱 URLs para acceder:
echo    • Aplicación Web: http://100.81.201.68:3000
echo    • API Backend: https://100.81.201.68:8001
echo    • Documentación: https://100.81.201.68:8001/docs
echo.
echo 💡 Para detener los servicios:
echo    • Cierra las ventanas del Backend y Frontend
echo    • O presiona Ctrl+C en cada ventana
echo.
echo 🎉 ¡Disfruta tu Biblioteca Inteligente con acceso móvil seguro!
echo.
pause
