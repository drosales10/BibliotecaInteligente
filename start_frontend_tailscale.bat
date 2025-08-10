@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Frontend Tailscale (Puerto 3000)

echo.
echo ========================================================================
echo 🌐 BIBLIOTECA INTELIGENTE - FRONTEND TAILSCALE
echo ========================================================================
echo 🌐 IP Tailscale: 100.81.201.68
echo 🔌 Puerto: 3000
echo 🔗 Conecta con Backend: https://100.81.201.68:8001
echo ========================================================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo 🔍 Verificando configuración...
echo 📁 Directorio actual: %CD%
echo.

REM Verificar si Node.js está disponible
echo 🔍 Verificando Node.js...
node --version
if errorlevel 1 (
    echo ❌ Node.js no está disponible
    echo 💡 Instala Node.js desde https://nodejs.org
    pause
    exit /b 1
)

REM Verificar si npm está disponible
echo 🔍 Verificando npm...
npm --version
if errorlevel 1 (
    echo ❌ npm no está disponible
    echo 💡 Reinstala Node.js para incluir npm
    pause
    exit /b 1
)

echo ✅ Verificaciones completadas
echo.

REM Cambiar al directorio del frontend
cd frontend

echo 📁 Cambiando al directorio frontend...
echo 📁 Directorio actual: %CD%
echo.

REM Verificar si el build existe
if not exist "build" (
    echo ❌ No se encontró el directorio build
    echo 💡 Ejecuta: npm run build
    echo.
    echo 🏗️  ¿Deseas construir la aplicación ahora? (S/N)
    choice /C SN /M "Construir aplicación"
    if errorlevel 2 (
        echo ❌ No se puede continuar sin el build
        pause
        exit /b 1
    )
    
    echo 🏗️  Construyendo aplicación...
    npm run build
    if errorlevel 1 (
        echo ❌ Error en la construcción
        pause
        exit /b 1
    )
)

echo 🚀 Iniciando Frontend con Tailscale...
echo 🌐 Estará disponible en: http://100.81.201.68:3000
echo.
echo ⚠️  IMPORTANTE: Solo accesible desde dispositivos en tu red Tailscale
echo.
echo ⏹️  Presiona Ctrl+C para detener el frontend
echo.

REM Iniciar el frontend
echo 🚀 Ejecutando: npm run serve
echo 📋 Los logs del frontend aparecerán a continuación...
echo.

REM Ejecutar npm run serve y capturar el código de salida
npm run serve
set exit_code=%errorlevel%

echo.
echo ⏹️  Frontend detenido
echo 💡 Código de salida: %exit_code%

if %exit_code% neq 0 (
    echo ❌ El frontend terminó con error (código: %exit_code%)
    echo 💡 Posibles causas:
    echo    - Error en la configuración del package.json
    echo    - Puerto 3000 ya está en uso
    echo    - Problema con la IP de Tailscale
    echo.
    echo 🔧 Para diagnosticar:
    echo    1. Verifica que Tailscale esté conectado
    echo    2. Comprueba que no haya otro servidor en puerto 3000
    echo    3. Revisa los mensajes de error arriba
) else (
    echo ✅ Frontend terminó correctamente
)

echo.
pause
