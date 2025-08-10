@echo off
chcp 65001 >nul
title Generando Certificado SSL Compatible

echo.
echo ========================================================================
echo 🔒 GENERANDO CERTIFICADO SSL COMPATIBLE PARA TAILSCALE
echo ========================================================================
echo 🌐 IP: 100.81.201.68
echo 🔧 Creando certificado con extensiones web compatibles
echo ========================================================================
echo.

cd /d "%~dp0"

REM Ir al directorio backend/ssl
cd backend\ssl

echo 📁 Directorio actual: %CD%
echo.

REM Crear archivo de configuración OpenSSL
echo 🔧 Creando configuración OpenSSL...
(
echo [req]
echo distinguished_name = req_distinguished_name
echo req_extensions = v3_req
echo prompt = no
echo.
echo [req_distinguished_name]
echo C = ES
echo ST = Madrid
echo L = Madrid
echo O = Biblioteca Inteligente
echo CN = 100.81.201.68
echo.
echo [v3_req]
echo basicConstraints = CA:FALSE
echo keyUsage = keyEncipherment, dataEncipherment, digitalSignature
echo extendedKeyUsage = serverAuth, clientAuth
echo subjectAltName = @alt_names
echo.
echo [alt_names]
echo IP.1 = 100.81.201.68
echo IP.2 = 127.0.0.1
echo DNS.1 = localhost
echo DNS.2 = *.tailscale
) > tailscale_ssl.conf

echo ✅ Configuración creada
echo.

echo 🔑 Generando clave privada...
openssl genrsa -out tailscale_key.pem 2048
if errorlevel 1 (
    echo ❌ Error generando clave privada
    pause
    exit /b 1
)
echo ✅ Clave privada generada

echo 📜 Generando certificado...
openssl req -new -x509 -key tailscale_key.pem -out tailscale_cert.pem -days 365 -config tailscale_ssl.conf -extensions v3_req
if errorlevel 1 (
    echo ❌ Error generando certificado
    pause
    exit /b 1
)
echo ✅ Certificado generado

echo 🔍 Verificando certificado...
openssl x509 -in tailscale_cert.pem -text -noout | findstr "Key Usage"
openssl x509 -in tailscale_cert.pem -text -noout | findstr "Extended Key Usage"
openssl x509 -in tailscale_cert.pem -text -noout | findstr "Subject Alternative Name" -A 1

echo.
echo ✅ Certificado SSL compatible generado exitosamente
echo 📁 Ubicación: %CD%\tailscale_cert.pem
echo 🔑 Clave: %CD%\tailscale_key.pem
echo.
echo 🔄 Ahora reinicia el backend para usar el nuevo certificado
echo.

REM Limpiar archivo temporal
del tailscale_ssl.conf

pause
