@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Backend SSL

echo.
echo ========================================
echo   Biblioteca Inteligente - Backend SSL
echo ========================================
echo.

echo 🔒 Verificando configuración SSL...
echo.

REM Verificar si existe el directorio SSL
if not exist "ssl" (
    echo 📁 Creando directorio SSL...
    mkdir ssl
)

REM Verificar si existen certificados SSL
if not exist "ssl\cert.pem" (
    echo 📜 Generando certificados SSL...
    echo.
    python generate_ssl.py
    if errorlevel 1 (
        echo.
        echo ❌ Error generando certificados SSL
        echo 💡 Asegúrate de tener OpenSSL instalado
        echo.
        pause
        exit /b 1
    )
    echo.
) else (
    echo ✅ Certificados SSL encontrados
)

echo.
echo 🚀 Iniciando servidor con SSL...
echo 📱 URL: https://192.168.100.6:8001
echo.
echo ⚠️  Nota: Los navegadores mostrarán una advertencia de seguridad
echo    porque es un certificado autofirmado. Esto es normal en desarrollo.
echo.

REM Iniciar el servidor
python start_server.py

echo.
echo ⏹️  Servidor detenido
pause
