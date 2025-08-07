# Configuración del Entorno Virtual de Python

Este proyecto utiliza un entorno virtual de Python para aislar las dependencias del entorno global de Windows.

## Requisitos Previos

- **Python 3.8 o superior** instalado en el sistema
- **Node.js** (para el frontend)

## Configuración Inicial

### 1. Configuración Automática (Recomendado)

Ejecuta el script de configuración automática:

```bash
setup_environment.bat
```

Este script:
- Verifica que Python esté instalado
- Crea un entorno virtual en la carpeta `venv/`
- Activa el entorno virtual
- Instala todas las dependencias del backend
- Instala las dependencias del frontend (si Node.js está disponible)

### 2. Configuración Manual

Si prefieres configurar manualmente:

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
venv\Scripts\activate.bat

# Instalar dependencias del backend
cd backend
pip install -r requirements.txt
cd ..

# Instalar dependencias del frontend
cd frontend
npm install
cd ..
```

## Uso Diario

### Activar el Entorno Virtual

```bash
venv\Scripts\activate.bat
```

### Ejecutar la Aplicación

```bash
start.bat
```

Este script activa automáticamente el entorno virtual y ejecuta tanto el backend como el frontend.

### Desactivar el Entorno Virtual

```bash
deactivate_env.bat
```

O manualmente:

```bash
deactivate
```

## Gestión del Entorno

### Limpiar el Entorno Virtual

Si necesitas recrear completamente el entorno virtual:

```bash
clean_environment.bat
```

### Verificar el Estado

Para verificar el estado completo del entorno virtual:

```bash
check_environment.bat
```

Este script verifica:
- Si Python está instalado
- Si el entorno virtual existe
- Si está activado
- Si las dependencias están instaladas
- Estado del frontend

También puedes verificar manualmente si el entorno virtual está activado buscando el prefijo `(venv)` en tu terminal.

## Estructura de Archivos

```
libreria-inteligente/
├── venv/                    # Entorno virtual de Python
├── setup_environment.bat    # Script de configuración inicial
├── start.bat               # Script para ejecutar la aplicación
├── stop.bat                # Script para detener la aplicación
├── deactivate_env.bat      # Script para desactivar el entorno
├── clean_environment.bat   # Script para limpiar el entorno
├── check_environment.bat   # Script para verificar el estado
├── backend/                # Código del backend
└── frontend/               # Código del frontend
```

## Ventajas del Entorno Virtual

1. **Aislamiento**: Las dependencias no interfieren con otros proyectos
2. **Control de versiones**: Cada proyecto puede usar versiones específicas
3. **Portabilidad**: Fácil de recrear en otros sistemas
4. **Limpieza**: Fácil de eliminar y recrear cuando sea necesario

## Solución de Problemas

### Error: "Python no está instalado"

Instala Python desde [python.org](https://python.org) y asegúrate de que esté en el PATH del sistema.

### Error: "No se pudo crear el entorno virtual"

Verifica que tienes permisos de escritura en el directorio del proyecto.

### Error: "No se pudieron instalar las dependencias"

- Verifica tu conexión a internet
- Intenta actualizar pip: `python -m pip install --upgrade pip`
- Si persiste, ejecuta `clean_environment.bat` y vuelve a ejecutar `setup_environment.bat`

### El entorno virtual no se activa

Asegúrate de ejecutar el script desde la raíz del proyecto donde está la carpeta `venv/`.

## Notas Importantes

- **Nunca** subas la carpeta `venv/` al control de versiones (ya está en `.gitignore`)
- Siempre activa el entorno virtual antes de trabajar en el proyecto
- Si agregas nuevas dependencias, actualiza `backend/requirements.txt`
- El entorno virtual es específico para Windows, para otros sistemas usa los comandos equivalentes 