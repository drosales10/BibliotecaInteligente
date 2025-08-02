# 📚 Mi Librería Inteligente

Mi Librería Inteligente es una aplicación web que utiliza la IA multimodal de Google Gemini para analizar y catalogar automáticamente tu colección de libros digitales (PDF y EPUB). Simplemente sube un libro, y la aplicación extraerá su portada, título, autor y le asignará una categoría, guardándolo todo en una base de datos local para que puedas explorar tu biblioteca fácilmente.

## ✨ Características

- **Subida Sencilla:** Arrastra y suelta o selecciona archivos PDF y EPUB.
- **Análisis con IA:** Utiliza Google Gemini para extraer metadatos clave de tus libros, incluso si no están presentes en el archivo.
- **Catalogación Automática:** Guarda los libros en una base de datos local.
- **Extracción de Portadas:** Intenta encontrar y guardar la imagen de la portada del libro.
- **Biblioteca Visual:** Explora todos tus libros en una vista de galería.
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

### 1. Clonar el Repositorio

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

### 2. Configurar el Backend

```bash
# Navega al directorio del backend
cd backend

# Crea y activa un entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
# source .venv/bin/activate

# Instala las dependencias de Python
pip install -r requirements.txt

# Crea la base de datos inicial
alembic upgrade head
```

### 3. Configurar las Variables de Entorno

En la raíz del proyecto, crea un archivo llamado `.env` y añade tu clave de API de Gemini. Puedes usar el archivo `.env.example` como plantilla.

**.env**
```
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"
```

### 4. Configurar el Frontend

```bash
# Desde la raíz del proyecto, navega al directorio del frontend
cd frontend

# Instala las dependencias de Node.js
npm install
```

### 5. ¡Ejecutar la Aplicación!

Necesitarás dos terminales abiertas.

- **En la Terminal 1 (para el Backend):**
  ```bash
  # Desde la carpeta 'backend' y con el entorno virtual activado
  uvicorn main:app --reload --port 8001
  ```

- **En la Terminal 2 (para el Frontend):**
  ```bash
  # Desde la carpeta 'frontend'
  npm start
  ```

¡Abre tu navegador en `http://localhost:3000` y empieza a construir tu librería inteligente!

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
