@echo off
chcp 65001 >nul
title Biblioteca Inteligente - Selector de Modo

echo.
echo ================================================================================
echo 📚 BIBLIOTECA INTELIGENTE - SELECTOR DE MODO DE DESPLIEGUE
echo ================================================================================
echo.
echo Selecciona el modo de despliegue que necesitas:
echo.
echo 🏠 [1] MODO LOCAL
echo     • Para desarrollo y carga de carpetas
echo     • URL: http://localhost:3000
echo     • File System Access API: ✅ Disponible
echo     • Acceso móvil: ❌ No disponible
echo.
echo 📶 [2] MODO WIFI 
echo     • Para acceso desde dispositivos en tu red WiFi
echo     • URL: http://192.168.100.6:3000
echo     • File System Access API: ❌ No disponible (usar ZIP)
echo     • Acceso móvil: ✅ Desde la misma WiFi
echo.
echo 🌐 [3] MODO TAILSCALE
echo     • Para acceso móvil seguro desde internet
echo     • URL: http://100.81.201.68:3000
echo     • File System Access API: ❌ No disponible (usar ZIP)
echo     • Acceso móvil: ✅ Desde cualquier lugar (requiere Tailscale)
echo.
echo ================================================================================

choice /C 123 /M "Selecciona el modo (1=Local, 2=WiFi, 3=Tailscale)"

if errorlevel 3 goto tailscale
if errorlevel 2 goto wifi
if errorlevel 1 goto local

:local
echo.
echo 🏠 Iniciando en MODO LOCAL...
call start_local.bat
goto end

:wifi
echo.
echo 📶 Iniciando en MODO WIFI...
call start_wifi.bat
goto end

:tailscale
echo.
echo 🌐 Iniciando en MODO TAILSCALE...
call start_tailscale.bat
goto end

:end
echo.
echo 👋 ¡Gracias por usar Biblioteca Inteligente!
pause
