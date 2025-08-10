@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Modo Seguro Tailscale

echo.
echo ================================================================================
echo 🌐 BIBLIOTECA INTELIGENTE - MODO SEGURO CON TAILSCALE
echo ================================================================================
echo 📱 Acceso seguro desde dispositivos móviles a través de Tailscale
echo 🔒 Conexión cifrada en red privada
echo ================================================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    echo 💡 Instala Python desde https://python.org
    echo.
    pause
    exit /b 1
)

REM Verificar si Tailscale está instalado
if not exist "C:\Program Files\Tailscale\tailscale.exe" (
    echo ❌ Tailscale no está instalado
    echo 💡 Instala Tailscale desde https://tailscale.com/download
    echo.
    pause
    exit /b 1
)

echo ✅ Verificaciones iniciales completadas
echo.

REM Preguntar sobre configuración de firewall
echo 🔥 ¿Deseas configurar automáticamente el firewall de Windows?
echo    Esto permitirá conexiones en los puertos 8001 y 3000
echo    (Solo necesario la primera vez)
echo.
choice /C SN /M "¿Configurar firewall? (S=Sí, N=No)"

if errorlevel 2 (
    echo ⏭️  Saltando configuración de firewall
) else (
    echo 🔧 Configurando firewall...
    powershell -ExecutionPolicy Bypass -File configure_firewall.ps1
)

echo.

REM Ejecutar el script principal de Python
echo 🚀 Iniciando Biblioteca Inteligente con Tailscale...
echo.

python start_tailscale_secure.py

echo.
echo ⏹️  Aplicación detenida
echo.
pause
