@echo off
echo ========================================
echo Configurando entorno virtual de Python
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor, instala Python desde https://python.org
    pause
    exit /b 1
)

echo Python detectado:
python --version
echo.

REM Crear directorio para el entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo Entorno virtual creado exitosamente
) else (
    echo El entorno virtual ya existe
)

echo.
echo ========================================
echo Activando entorno virtual...
echo ========================================
echo.

REM Activar el entorno virtual
call venv\Scripts\activate.bat

echo Entorno virtual activado
echo.

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

echo.
echo ========================================
echo Instalando dependencias del backend...
echo ========================================
echo.

REM Instalar dependencias del backend
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Instalando dependencias del frontend...
echo ========================================
echo.

REM Verificar si Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ADVERTENCIA: Node.js no está instalado
    echo El frontend no se puede configurar sin Node.js
    echo Instala Node.js desde https://nodejs.org
) else (
    echo Node.js detectado:
    node --version
    echo.
    
    REM Instalar dependencias del frontend
    cd frontend
    npm install
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias del frontend
        pause
        exit /b 1
    )
    cd ..
)

echo.
echo ========================================
echo Configuración completada exitosamente!
echo ========================================
echo.
echo Para activar el entorno virtual en el futuro:
echo   venv\Scripts\activate.bat
echo.
echo Para ejecutar la aplicación:
echo   start.bat
echo.
pause 