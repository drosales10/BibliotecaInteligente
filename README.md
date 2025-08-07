# 📚 Mi Biblioteca Inteligente

Mi Librería Inteligente es una aplicación web que utiliza la IA multimodal de Google Gemini para analizar y catalogar automáticamente tu colección de libros digitales (PDF y EPUB). Simplemente sube un libro, y la aplicación extraerá su portada, título, autor y le asignará una categoría, guardándolo todo en una base de datos local para que puedas explorar tu biblioteca fácilmente.

## ✨ Características Principales

- **Subida Sencilla:** Arrastra y suelta o selecciona archivos PDF y EPUB para añadir a tu biblioteca.
- **Análisis Inteligente con IA:** Utiliza Google Gemini para extraer metadatos clave (título, autor, categoría) de tus libros, incluso si no están presentes en el archivo, y encuentra la portada.
- **Lectura Integrada:** Lee tus libros (PDF y EPUB) directamente dentro de la aplicación, sin necesidad de software externo. Los PDF se abren en una nueva pestaña para una mejor experiencia.
- **Conversor EPUB a PDF:** Convierte tus archivos EPUB a formato PDF directamente desde la aplicación. El PDF resultante se abre automáticamente en una nueva pestaña.
- **Catalogación Automática:** Guarda los libros y sus metadatos en una base de datos local.
- **Biblioteca Visual:** Explora todos tus libros en una vista de galería intuitiva.
- **Filtros por Categoría:** Filtra tu biblioteca por las categorías asignadas por la IA.
- **Buscador Integrado:** Busca libros instantáneamente por título, autor o categoría.
- **Gestión Completa:** Elimina libros individuales o categorías enteras con un solo clic.
- **Acceso Directo:** Abre los archivos originales de tus libros directamente desde la aplicación.

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React (JavaScript)
- **IA:** Google Gemini Pro
- **Base de Datos:** SQLite
- **Manejo de Libros:** PyMuPDF (para PDF), EbookLib (para EPUB)

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

### Prerrequisitos

- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js y npm](https://nodejs.org/en/)
- Una clave de API de **Google Gemini**. Puedes obtenerla en [Google AI Studio](https://aistudio.google.com/app/apikey).

### Dependencias Adicionales (Para la Conversión EPUB a PDF)

La herramienta de conversión de EPUB a PDF requiere la instalación de **GTK3**. Si no instalas esta dependencia, el resto de la aplicación funcionará correctamente, pero la herramienta de conversión mostrará un error al intentar convertir.

## 🚀 Instalación Rápida con Entorno Virtual

### Requisitos Previos

- **Python 3.9+** instalado en el sistema
- **Node.js 18+** (recomendado: 20.10.0)
- **Git** (opcional, para clonar el repositorio)

### Instalación de Miniconda (Windows)

1. **Descargar Miniconda:**
   - Ir a [Miniconda Downloads](https://docs.conda.io/en/latest/miniconda.html)
   - Descargar la versión para Windows 64-bit

2. **Instalar Miniconda:**
   - Ejecutar el instalador como administrador
   - Marcar "Add Miniconda3 to my PATH environment variable"
   - Completar la instalación

3. **Verificar instalación:**
   ```bash
   python --version  # Debe mostrar Python 3.13.2
   ```

### 1. Clonar el Repositorio

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

### 2. Configurar el Entorno Virtual (Recomendado)

```bash
# Configuración automática del entorno virtual
setup_environment.bat
```

Este script:
- Crea un entorno virtual de Python
- Instala todas las dependencias del backend
- Instala las dependencias del frontend
- Configura todo automáticamente

### 3. Configuración Manual (Alternativa)

Si prefieres configurar manualmente:

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
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

### 4. Configurar las Variables de Entorno

En la raíz del proyecto, crea un archivo llamado `.env` y añade tu clave de API de Gemini. Puedes usar el archivo `.env.example` como plantilla.

**.env**
```
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"
```

### 5. ¡Ejecutar la Aplicación!

```bash
# Ejecutar todo con un solo comando
start.bat
```

Este script:
- Activa automáticamente el entorno virtual
- Inicia el servidor backend en http://localhost:8001
- Inicia el servidor frontend en http://localhost:3000

¡Abre tu navegador en `http://localhost:3000` y empieza a construir tu librería inteligente!

## 🔧 Gestión del Entorno Virtual

### Comandos Útiles

```bash
# Activar entorno virtual manualmente
venv\Scripts\activate.bat

# Desactivar entorno virtual
deactivate_env.bat

# Limpiar y recrear entorno virtual
clean_environment.bat

# Detener todos los servidores
stop.bat
```

Para más información sobre el entorno virtual, consulta [ENTORNO_VIRTUAL.md](ENTORNO_VIRTUAL.md).

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
