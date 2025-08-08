@echo off
echo ========================================
echo    Iniciando Frontend - Libreria Inteligente
echo ========================================
echo.

REM Verificar si Node.js está instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no está instalado o no está en el PATH
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar si el backend está ejecutándose
echo Verificando conexión con el backend...
curl -s http://localhost:8001/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: El backend no parece estar ejecutándose en puerto 8001
    echo Asegúrate de que el backend esté iniciado antes de continuar
    echo.
    set /p continue="¿Continuar de todas formas? (s/n): "
    if /i not "%continue%"=="s" exit /b 1
)

REM Limpiar caché de npm si es necesario
echo Limpiando caché de npm...
npm cache clean --force

REM Instalar dependencias si es necesario
if not exist "node_modules" (
    echo Instalando dependencias...
    npm install
)

REM Intentar diferentes métodos de inicio
echo.
echo Intentando iniciar el servidor de desarrollo...

REM Método 1: React Scripts normal
echo Método 1: React Scripts...
npm start
if %errorlevel% equ 0 (
    echo Servidor iniciado exitosamente con React Scripts
    exit /b 0
)

REM Método 2: React Scripts con OpenSSL legacy
echo.
echo Método 2: React Scripts con OpenSSL legacy...
npx react-scripts start --openssl-legacy-provider
if %errorlevel% equ 0 (
    echo Servidor iniciado exitosamente con OpenSSL legacy
    exit /b 0
)

REM Método 3: Puerto alternativo
echo.
echo Método 3: Puerto alternativo...
set PORT=3001
npm start
if %errorlevel% equ 0 (
    echo Servidor iniciado exitosamente en puerto 3001
    exit /b 0
)

echo.
echo ERROR: No se pudo iniciar el servidor con ningún método
echo.
echo Opciones disponibles:
echo 1. Verificar que no haya otros procesos usando el puerto 3000
echo 2. Usar Vite como alternativa: npm install vite @vitejs/plugin-react
echo 3. Revisar los logs de error arriba
echo.
pause 