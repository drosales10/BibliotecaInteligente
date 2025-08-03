# 🔧 Solución de Problemas - Instalación y Configuración

## Problemas Comunes y Soluciones

### ❌ Error: "No module named 'models'" en Alembic

**Descripción del problema:**
```
ModuleNotFoundError: No module named 'models'
```

**Causa:**
- Alembic no puede encontrar el módulo `models` porque Python no tiene el directorio del proyecto en su path
- Configuración incorrecta del archivo `env.py` de Alembic

**Solución:**
1. **Editar el archivo `backend/alembic/env.py`:**
   ```python
   import sys
   import os
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   
   from database import Base
   import models  # Importa los modelos para que Alembic los detecte
   target_metadata = Base.metadata
   ```

2. **Usar el Python correcto:**
   - Evitar usar Python de MSYS2 que tiene problemas de compatibilidad
   - Usar Python de Miniconda: `& "C:\Users\Javier Rosales\miniconda3\python.exe" -m alembic upgrade head`

### ❌ Error: "alembic: The term 'alembic' is not recognized"

**Descripción del problema:**
```
alembic: The term 'alembic' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

**Causa:**
- Alembic no está instalado o no está en el PATH
- Uso incorrecto del comando

**Solución:**
1. **Instalar Alembic:**
   ```bash
   pip install alembic
   ```

2. **Usar el módulo Python:**
   ```bash
   python -m alembic upgrade head
   ```

### ❌ Error: Problemas de compatibilidad con Python 3.12 de MSYS2

**Descripción del problema:**
```
Python reports SOABI: cpython-312
Unsupported platform: 312
Rust not found, installing into a temporary directory
```

**Causa:**
- Python 3.12 de MSYS2 tiene problemas de compatibilidad con algunas dependencias
- Falta de herramientas de compilación

**Solución:**
1. **Usar Miniconda en lugar de MSYS2:**
   ```bash
   # Usar Python de Miniconda
   & "C:\Users\Javier Rosales\miniconda3\python.exe" -m pip install [dependencias]
   ```

2. **Instalar dependencias básicas primero:**
   ```bash
   pip install fastapi uvicorn sqlalchemy alembic python-dotenv
   ```

### ❌ Error: "react-scripts no se reconoce como un comando"

**Descripción del problema:**
```
"react-scripts" no se reconoce como un comando interno o externo
```

**Causa:**
- Las dependencias de Node.js no están instaladas
- Ejecutar npm desde el directorio incorrecto

**Solución:**
1. **Navegar al directorio frontend:**
   ```bash
   cd frontend
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Iniciar el servidor de desarrollo:**
   ```bash
   npm start
   ```

### ❌ Error: "Failed to connect to localhost port 8001"

**Descripción del problema:**
```
curl: (7) Failed to connect to localhost port 8001 after 2225 ms: Could not connect to server
```

**Causa:**
- El servidor backend no está ejecutándose
- Puerto ocupado por otro proceso
- Error en la configuración del servidor

**Solución:**
1. **Verificar procesos Python:**
   ```bash
   Get-Process python -ErrorAction SilentlyContinue
   ```

2. **Terminar procesos si es necesario:**
   ```bash
   taskkill /f /im python.exe
   ```

3. **Iniciar el servidor manualmente:**
   ```bash
   cd backend
   & "C:\Users\Javier Rosales\miniconda3\python.exe" -m uvicorn main:app --reload --port 8001
   ```

## ✅ Configuración Recomendada

### Entorno de Desarrollo
- **Python**: Miniconda (evitar MSYS2)
- **Node.js**: Versión 20.10.0 o superior
- **Base de datos**: SQLite (automática)

### Scripts de Inicio
- **start.bat**: Inicia backend y frontend automáticamente
- **start_backend.bat**: Solo el backend con Python de Miniconda

### Verificación de Instalación
```bash
# Verificar Python
& "C:\Users\Javier Rosales\miniconda3\python.exe" -c "import fastapi, uvicorn, sqlalchemy, alembic; print('OK')"

# Verificar Node.js
node --version

# Verificar servidores
curl http://localhost:8001  # Backend
curl http://localhost:3000  # Frontend
```

## 📞 Obtener Ayuda

Si encuentras un problema no documentado aquí:
1. Revisar los logs de error
2. Verificar la configuración del entorno
3. Crear un issue en el repositorio con los detalles del error 