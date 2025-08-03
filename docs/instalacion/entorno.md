# ⚙️ Configuración del Entorno de Desarrollo

## 📋 Requisitos del Sistema

### Software Requerido
- **Windows 10/11** (sistema operativo principal)
- **Python 3.9+** (Miniconda - **única fuente de Python**)
- **Node.js 18+** (recomendado: 20.10.0)
- **npm** (incluido con Node.js)

### Herramientas Opcionales
- **Git** (para control de versiones)
- **Visual Studio Code** (editor recomendado)
- **Postman** (para probar la API)

## 🐍 Configuración de Python

### ✅ Estado Actual: Solo Miniconda
- **MSYS2**: Desinstalado (ya no necesario)
- **Python**: Miniconda 3.13.2 (única fuente)
- **Ubicación**: `C:\Users\Javier Rosales\miniconda3\python.exe`

### Instalación de Miniconda
1. **Descargar Miniconda:**
   - Ir a [Miniconda Downloads](https://docs.conda.io/en/latest/miniconda.html)
   - Descargar la versión para Windows 64-bit

2. **Instalar Miniconda:**
   - Ejecutar el instalador como administrador
   - Marcar "Add Miniconda3 to my PATH environment variable"
   - Completar la instalación

3. **Verificar instalación:**
   ```bash
   conda --version
   python --version
   ```

### Configuración del Entorno Python
```bash
# Ruta del Python de Miniconda
C:\Users\Javier Rosales\miniconda3\python.exe

# Verificar que estamos usando el Python correcto
python --version  # Debe mostrar Python 3.13.2
python -c "import sys; print(sys.executable)"  # Debe mostrar Miniconda
```

### Dependencias de Python
```bash
# Instalar dependencias básicas
python -m pip install fastapi uvicorn sqlalchemy alembic python-dotenv

# Instalar dependencias adicionales
python -m pip install python-multipart ebooklib google-generativeai beautifulsoup4 PyMuPDF
```

## 🟢 Configuración de Node.js

### Instalación de Node.js
1. **Descargar Node.js:**
   - Ir a [Node.js Downloads](https://nodejs.org/)
   - Descargar la versión LTS (20.x.x)

2. **Instalar Node.js:**
   - Ejecutar el instalador
   - Seguir las opciones por defecto
   - Completar la instalación

3. **Verificar instalación:**
   ```bash
   node --version
   npm --version
   ```

### Configuración del Frontend
```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Verificar instalación
npm list --depth=0
```

## 🗄️ Configuración de la Base de Datos

### SQLite (Automática)
- **Ubicación:** `library.db` en la raíz del proyecto
- **Configuración:** Automática con SQLAlchemy
- **Migraciones:** Gestionadas por Alembic

### Configuración de Alembic
```bash
# Ejecutar migraciones
cd backend
python -m alembic upgrade head
```

## 🔧 Variables de Entorno

### Archivo .env
Crear archivo `.env` en la raíz del proyecto:
```env
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"
```

### Obtener API Key de Gemini
1. Ir a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crear una nueva API key
3. Copiar la key al archivo `.env`

## 🚀 Scripts de Inicio

### Script Principal (start.bat)
```batch
@echo off
echo ========================================
echo   Iniciando Servidores de la Libreria
echo ========================================

REM Iniciar el servidor del Backend en una nueva ventana
echo Iniciando Backend en http://localhost:8001 ...
START "Backend" cmd /c "cd backend && python -m uvicorn main:app --reload --port 8001"

REM Iniciar el servidor del Frontend en una nueva ventana
echo Iniciando Frontend en http://localhost:3000 ...
START "Frontend" cmd /c "cd frontend && npm start"

echo.
echo Servidores iniciados en segundo plano.
echo Puedes cerrar esta ventana.
timeout /t 5 >nul
```

### Script del Backend (start_backend.bat)
```batch
@echo off
echo Iniciando el backend de la Libreria Inteligente...
echo.

REM Verificar que Python existe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: No se encontró Python
    echo Por favor, verifica que Miniconda esté instalado correctamente.
    pause
    exit /b 1
)

echo Usando Python: 
python --version
echo.

REM Ejecutar las migraciones de la base de datos
echo Ejecutando migraciones de la base de datos...
python -m alembic upgrade head

REM Iniciar el servidor
echo.
echo Iniciando el servidor backend en http://localhost:8001
echo Presiona Ctrl+C para detener el servidor
echo.
python -m uvicorn main:app --reload --port 8001

pause
```

## ✅ Verificación de la Configuración

### Comandos de Verificación
```bash
# Verificar Python (debe ser Miniconda)
python --version  # Debe mostrar Python 3.13.2
python -c "import fastapi, uvicorn, sqlalchemy, alembic, google.generativeai; print('Python OK')"

# Verificar Node.js
node --version  # Debe mostrar v20.10.0
npm --version

# Verificar servidores
curl http://localhost:8001  # Backend
curl http://localhost:3000  # Frontend
```

### Estado Esperado
- ✅ Python de Miniconda funcionando (única fuente)
- ✅ Todas las dependencias de Python instaladas
- ✅ Node.js y npm funcionando
- ✅ Dependencias del frontend instaladas
- ✅ Base de datos SQLite creada
- ✅ Servidores backend y frontend ejecutándose
- ✅ MSYS2 desinstalado (sin conflictos)

## 🚨 Problemas Comunes

### ✅ MSYS2 Desinstalado
**Estado:** MSYS2 ha sido desinstalado exitosamente
**Beneficio:** No más conflictos entre Python de MSYS2 y Miniconda

### Dependencias de Node.js
**Problema:** `react-scripts` no encontrado
**Solución:** Ejecutar `npm install` en el directorio `frontend`

### Puerto Ocupado
**Problema:** Error al iniciar servidores
**Solución:** Terminar procesos existentes con `taskkill /f /im python.exe`

## 📚 Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de React](https://reactjs.org/docs/)
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentación de Alembic](https://alembic.sqlalchemy.org/) 