@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =========================================
::  Biblioteca Inteligente - Inicio Seguro (CMD)
:: =========================================

title Biblioteca Inteligente - Inicio Seguro (CMD)

:: Raíz del proyecto (directorio de este script)
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%
set BACKEND_DIR=%ROOT%\backend
set FRONTEND_DIR=%ROOT%\frontend
set VENV_PY=%ROOT%\venv\Scripts\python.exe

:: Puertos
set FRONT_PORT=3000
set BACK_PORT=8001

:: Función: pausa breve
set SLP=ping -n 2 127.0.0.1 >nul

:: Función: detener procesos en un puerto
:KILL_PORT
:: %1 = puerto
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r ":%1 .*LISTENING"') do (
  taskkill /F /PID %%a >nul 2>&1
)
exit /b 0

:: Función: obtener IP LAN preferida (prioriza 192.168.100.6)
:GET_LAN_IP
set LAN_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1 delims=(" %%b in ("%%a") do (
    set ip=%%b
    set ip=!ip: =!
    if "!ip!"=="192.168.100.6" set LAN_IP=!ip!
  )
)
if not "%LAN_IP%"=="" goto :eof
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1 delims=(" %%b in ("%%a") do (
    set ip=%%b
    set ip=!ip: =!
    echo !ip!| findstr /r "^192\.168\..* ^10\..* ^172\.(1[6-9]|2[0-9]|3[0-1])\..*" >nul
    if !errorlevel! == 0 if "%LAN_IP%"=="" set LAN_IP=!ip!
  )
)
if "%LAN_IP%"=="" set LAN_IP=192.168.100.6
exit /b 0

:: Función: obtener IP Tailscale (100.64.0.0/10)
:GET_TS_IP
set TS_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1 delims=(" %%b in ("%%a") do (
    set ip=%%b
    set ip=!ip: =!
    echo !ip!| findstr /r "^100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\..*" >nul
    if !errorlevel! == 0 if "%TS_IP%"=="" set TS_IP=!ip!
  )
)
if "%TS_IP%"=="" set TS_IP=100.81.201.68
exit /b 0

:: Función: crear reglas de firewall
:FIREWALL_CREATE
setlocal
set TSCIDR=100.64.0.0/10
netsh advfirewall firewall add rule name="Biblioteca Backend SSL 8001 (Privado)" dir=in action=allow protocol=TCP localport=%BACK_PORT% profile=private,domain >nul 2>&1
netsh advfirewall firewall add rule name="Biblioteca Backend SSL 8001 (Tailscale)" dir=in action=allow protocol=TCP localport=%BACK_PORT% profile=private,domain remoteip=%TSCIDR% >nul 2>&1
netsh advfirewall firewall add rule name="Biblioteca Frontend 3000 (Privado)" dir=in action=allow protocol=TCP localport=%FRONT_PORT% profile=private,domain >nul 2>&1
netsh advfirewall firewall add rule name="Biblioteca Frontend 3000 (Tailscale)" dir=in action=allow protocol=TCP localport=%FRONT_PORT% profile=private,domain remoteip=%TSCIDR% >nul 2>&1
endlocal
exit /b 0

:: Función: eliminar reglas de firewall
:FIREWALL_DELETE
netsh advfirewall firewall delete rule name="Biblioteca Backend SSL 8001 (Privado)" >nul 2>&1
netsh advfirewall firewall delete rule name="Biblioteca Backend SSL 8001 (Tailscale)" >nul 2>&1
netsh advfirewall firewall delete rule name="Biblioteca Frontend 3000 (Privado)" >nul 2>&1
netsh advfirewall firewall delete rule name="Biblioteca Frontend 3000 (Tailscale)" >nul 2>&1
exit /b 0

:MAIN
echo [INFO] Deteniendo procesos en puertos %FRONT_PORT% y %BACK_PORT%
call :KILL_PORT %FRONT_PORT%
call :KILL_PORT %BACK_PORT%

call :GET_LAN_IP
call :GET_TS_IP

:MENU
echo.
echo =============================================
echo  Biblioteca Inteligente - Inicio Seguro (CMD)
echo =============================================
echo  1^) Local (HTTP, solo este equipo)
echo  2^) WiFi  (HTTPS, IP local %LAN_IP%)
echo  3^) Tailscale (HTTPS, IP %TS_IP%)
echo  5^) Configurar Firewall (crear reglas 3000/8001)
echo  6^) Eliminar Reglas de Firewall creadas
echo  4^) Salir
echo.
set /p CH=Selecciona una opcion ^(1-6^): 

if "%CH%"=="1" goto :LOCAL
if "%CH%"=="2" goto :WIFI
if "%CH%"=="3" goto :TS
if "%CH%"=="5" goto :FWC
if "%CH%"=="6" goto :FWD
if "%CH%"=="4" goto :END
echo [WARN] Opcion invalida.
goto :MENU

:LOCAL
echo.
echo [OK]   Modo Local (HTTP)
set HOST=127.0.0.1
set PORT=%BACK_PORT%
set USE_SSL=false
set LOG_LEVEL=info
set RELOAD=false
set ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000

:: Backend en nueva ventana
setlocal
set PATH=%ROOT%\venv\Scripts;%BACKEND_DIR%;%PATH%
start "Backend (HTTP)" cmd /k "cd /d "%BACKEND_DIR%" & set VIRTUAL_ENV=%ROOT%\venv & set HOST=%HOST% & set PORT=%PORT% & set USE_SSL=%USE_SSL% & set LOG_LEVEL=%LOG_LEVEL% & set RELOAD=%RELOAD% & set ALLOWED_ORIGINS=%ALLOWED_ORIGINS% & "%VENV_PY%" start_server.py"
endlocal
%SLP%

:: Frontend en nueva ventana
start "Frontend (React Dev Server)" cmd /k "cd /d "%FRONTEND_DIR%" & npm start"
%SLP%
goto :END

:WIFI
echo.
echo [OK]   Modo WiFi (HTTPS) - IP: %LAN_IP%
call :FIREWALL_CREATE
set HOST=0.0.0.0
set PORT=%BACK_PORT%
set USE_SSL=true
set LOG_LEVEL=info
set RELOAD=false
set ALLOWED_ORIGINS=http://%LAN_IP%:3000,https://%LAN_IP%:3000,http://localhost:3000,https://localhost:3000

:: Backend en nueva ventana (SSL)
setlocal
set PATH=%ROOT%\venv\Scripts;%BACKEND_DIR%;%PATH%
start "Backend (Uvicorn/SSL)" cmd /k "cd /d "%BACKEND_DIR%" & set VIRTUAL_ENV=%ROOT%\venv & set HOST=%HOST% & set PORT=%PORT% & set USE_SSL=%USE_SSL% & set LOG_LEVEL=%LOG_LEVEL% & set RELOAD=%RELOAD% & set ALLOWED_ORIGINS=%ALLOWED_ORIGINS% & "%VENV_PY%" start_server.py"
endlocal
%SLP%

:: Frontend en nueva ventana (apuntando al backend SSL)
start "Frontend (React Dev Server)" cmd /k "cd /d "%FRONTEND_DIR%" & set REACT_APP_API_BASE_URL=https://%LAN_IP%:%BACK_PORT% & set HOST=0.0.0.0 & npm start"
%SLP%
goto :END

:TS
echo.
echo [OK]   Modo Tailscale (HTTPS) - IP: %TS_IP%
call :FIREWALL_CREATE
set HOST=0.0.0.0
set PORT=%BACK_PORT%
set USE_SSL=true
set LOG_LEVEL=info
set RELOAD=false
set ALLOWED_ORIGINS=http://%TS_IP%:3000,https://%TS_IP%:3000,http://localhost:3000,https://localhost:3000

:: Backend en nueva ventana (SSL)
setlocal
set PATH=%ROOT%\venv\Scripts;%BACKEND_DIR%;%PATH%
start "Backend (Uvicorn/SSL)" cmd /k "cd /d "%BACKEND_DIR%" & set VIRTUAL_ENV=%ROOT%\venv & set HOST=%HOST% & set PORT=%PORT% & set USE_SSL=%USE_SSL% & set LOG_LEVEL=%LOG_LEVEL% & set RELOAD=%RELOAD% & set ALLOWED_ORIGINS=%ALLOWED_ORIGINS% & "%VENV_PY%" start_server.py"
endlocal
%SLP%

:: Frontend en nueva ventana (apuntando al backend SSL)
start "Frontend (React Dev Server)" cmd /k "cd /d "%FRONTEND_DIR%" & set REACT_APP_API_BASE_URL=https://%TS_IP%:%BACK_PORT% & set HOST=0.0.0.0 & npm start"
%SLP%
goto :END

:FWC
echo [INFO] Creando reglas de firewall (puertos %FRONT_PORT% y %BACK_PORT%)
call :FIREWALL_CREATE
echo [OK]   Reglas configuradas.
goto :MENU

:FWD
echo [INFO] Eliminando reglas de firewall
call :FIREWALL_DELETE
echo [OK]   Reglas eliminadas.
goto :MENU

:END
echo.
echo [OK]   Procesos iniciados en ventanas separadas. Para detenerlos, cierra esas ventanas o vuelve a ejecutar este script.
exit /b 0



