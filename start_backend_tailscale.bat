@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Backend Tailscale (Puerto 8001)

echo.
echo ========================================================================
echo 🚀 BIBLIOTECA INTELIGENTE - BACKEND TAILSCALE
echo ========================================================================
echo 🌐 IP Tailscale: 100.81.201.68
echo 🔌 Puerto: 8001
echo 🔒 SSL: Habilitado
echo ========================================================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo 🔍 Verificando configuración...
echo 📁 Directorio actual: %CD%
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está disponible
    echo 💡 Asegúrate de que Python esté instalado y en el PATH
    pause
    exit /b 1
)

REM Verificar si Tailscale está disponible
if not exist "C:\Program Files\Tailscale\tailscale.exe" (
    echo ❌ Tailscale no está instalado
    echo 💡 Instala Tailscale desde https://tailscale.com/download
    pause
    exit /b 1
)

echo ✅ Verificaciones completadas
echo.

echo 🚀 Iniciando Backend con Tailscale...
echo 🌐 Estará disponible en: https://100.81.201.68:8001
echo 📖 Documentación API: https://100.81.201.68:8001/docs
echo.
echo ⚠️  IMPORTANTE: Solo accesible desde dispositivos en tu red Tailscale
echo.
echo ⏹️  Presiona Ctrl+C para detener el backend
echo.

REM Iniciar el backend
python start_tailscale_backend.py

echo.
echo ⏹️  Backend detenido
pause
