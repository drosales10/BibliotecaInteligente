# 📚 Mi Biblioteca Inteligente

Mi Biblioteca Inteligente es una aplicación web avanzada que utiliza la IA multimodal de Google Gemini para analizar y catalogar automáticamente tu colección de libros digitales (PDF y EPUB). La aplicación ofrece almacenamiento en la nube con Google Drive, procesamiento masivo, herramientas avanzadas y una interfaz moderna con modo oscuro.

## ✨ Características Principales

### 📖 **Gestión de Libros**
- **Subida Sencilla:** Arrastra y suelta o selecciona archivos PDF y EPUB para añadir a tu biblioteca
- **Carga Masiva:** Sube múltiples libros simultáneamente desde archivos ZIP o carpetas
- **Carga desde Google Drive:** Importa libros directamente desde carpetas de Google Drive
- **Análisis Inteligente con IA:** Utiliza Google Gemini para extraer metadatos clave (título, autor, categoría) automáticamente
- **Detección de Duplicados:** Sistema inteligente que evita libros duplicados por nombre, título o autor
- **Edición de Libros:** Modifica título, autor, categoría y portada de cualquier libro
- **Gestión Completa:** Elimina libros individuales, múltiples libros o categorías enteras

### ☁️ **Almacenamiento en la Nube**
- **Google Drive Integration:** Almacenamiento exclusivo en la nube con organización automática
- **Estructura Organizada:** Los libros se organizan automáticamente por categorías y letras A-Z
- **Sincronización Automática:** Todos los cambios se reflejan instantáneamente en Google Drive
- **Ahorro de Espacio:** Los archivos no ocupan espacio local, solo se descargan temporalmente para lectura
- **Acceso Universal:** Accede a tu biblioteca desde cualquier dispositivo con conexión a internet

### 🖼️ **Gestión de Portadas**
- **Extracción Automática:** Extrae portadas directamente de archivos PDF y EPUB
- **Búsqueda Online:** Busca portadas en internet cuando no están disponibles en el archivo
- **Búsqueda Masiva:** Encuentra portadas para múltiples libros simultáneamente
- **Subida Manual:** Actualiza portadas subiendo imágenes personalizadas
- **Limpieza Automática:** Elimina portadas huérfanas y archivos temporales

### 📚 **Lectura y Conversión**
- **Lectura Integrada:** Lee tus libros (PDF y EPUB) directamente dentro de la aplicación
- **Conversor EPUB a PDF:** Convierte archivos EPUB a formato PDF con un clic
- **Apertura en Nueva Pestaña:** Los PDF se abren en una nueva pestaña para mejor experiencia
- **Descarga Directa:** Descarga los archivos originales directamente desde la aplicación

### 🔍 **Búsqueda y Filtrado**
- **Búsqueda Avanzada:** Busca por título, autor, categoría o cualquier palabra clave
- **Filtros Inteligentes:** Filtra por categoría, estado de sincronización o ubicación
- **Paginación Optimizada:** Navega por grandes bibliotecas con paginación eficiente
- **Búsqueda en Tiempo Real:** Resultados instantáneos mientras escribes

### 🛠️ **Herramientas Avanzadas**
- **Panel de Herramientas:** Acceso centralizado a todas las utilidades
- **Conversor de Formatos:** Convierte EPUB a PDF sin software externo
- **Limpieza de Archivos:** Elimina archivos temporales y portadas huérfanas
- **Estado de Google Drive:** Monitoreo en tiempo real del estado de la nube
- **Health Checks:** Verificación automática de la salud del sistema

### 🎨 **Interfaz Moderna**
- **Modo Oscuro:** Interfaz elegante con soporte completo para modo oscuro
- **Diseño Responsivo:** Funciona perfectamente en dispositivos móviles y de escritorio
- **Lazy Loading:** Carga de imágenes optimizada para mejor rendimiento
- **Indicadores Visuales:** Muestra claramente la ubicación de cada libro (local/nube)
- **Animaciones Suaves:** Transiciones fluidas y feedback visual

### 🔧 **Características Técnicas**
- **Procesamiento Concurrente:** Hasta 4 libros procesados simultáneamente
- **Caché Inteligente:** Sistema de caché para optimizar consultas a Google Drive
- **Reconexión Automática:** Manejo robusto de errores de conexión
- **Logging Detallado:** Registros completos para debugging y monitoreo
- **API RESTful:** Interfaz de programación completa y bien documentada

## 🛠️ Tecnologías Utilizadas

### **Backend**
- **Python 3.9+:** Lenguaje principal del servidor
- **FastAPI:** Framework web moderno y rápido
- **SQLAlchemy:** ORM para gestión de base de datos
- **Alembic:** Migraciones de base de datos
- **Google Drive API:** Integración completa con Google Drive
- **Google Gemini Pro:** IA multimodal para análisis de libros
- **PyMuPDF:** Procesamiento avanzado de archivos PDF
- **EbookLib:** Manejo de archivos EPUB

### **Frontend**
- **React 18:** Biblioteca de interfaz de usuario
- **JavaScript ES6+:** Lenguaje de programación moderno
- **CSS3:** Estilos avanzados con variables CSS
- **Vite:** Herramienta de construcción rápida
- **React Router:** Navegación entre páginas
- **Context API:** Gestión de estado global

### **Base de Datos y Almacenamiento**
- **SQLite:** Base de datos local ligera
- **Google Drive:** Almacenamiento principal en la nube
- **Sistema de Caché:** Optimización de rendimiento

## 🚀 Instalación y Puesta en Marcha

### Prerrequisitos

- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/en/) (recomendado: 20.10.0)
- Una clave de API de **Google Gemini**. Puedes obtenerla en [Google AI Studio](https://aistudio.google.com/app/apikey).
- Configuración de **Google Cloud Console** para Google Drive (opcional pero recomendado)

### Dependencias Adicionales

La herramienta de conversión de EPUB a PDF requiere la instalación de **GTK3**. Si no instalas esta dependencia, el resto de la aplicación funcionará correctamente, pero la herramienta de conversión mostrará un error al intentar convertir.

## 🚀 Instalación Rápida con Entorno Virtual

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

En la raíz del proyecto, crea un archivo llamado `.env` y añade tu clave de API de Gemini:

**.env**
```
GEMINI_API_KEY="TU_API_KEY_DE_GEMINI_AQUI"
```

### 5. Configurar Google Drive (Opcional pero Recomendado)

Para usar el almacenamiento en la nube:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Drive
4. Crea credenciales OAuth 2.0 para aplicación de escritorio
5. Descarga el archivo JSON de credenciales
6. Renómbralo a `credentials.json` y colócalo en la carpeta `backend/`
7. Ejecuta: `python setup_google_drive.py`

### 6. ¡Ejecutar la Aplicación!

```bash
# Ejecutar todo con un solo comando
start.bat
```

Este script:
- Activa automáticamente el entorno virtual
- Inicia el servidor backend en http://localhost:8001
- Inicia el servidor frontend en http://localhost:3000

¡Abre tu navegador en `http://localhost:3000` y empieza a construir tu biblioteca inteligente!

## 🔧 Gestión del Entorno Virtual

### Comandos Útiles

```bash
# Activar entorno virtual manualmente
venv\Scripts\activate.bat

# Desactivar entorno virtual
deactivate_env.bat

# Limpiar y recrear entorno virtual
clean_environment.bat

# Verificar estado del entorno
check_environment.bat

# Detener todos los servidores
stop.bat
```

## 📁 Estructura del Proyecto

```
BibliotecaInteligente/
├── backend/                 # Servidor Python/FastAPI
│   ├── main.py             # API principal
│   ├── google_drive_manager.py  # Gestión de Google Drive
│   ├── crud.py             # Operaciones de base de datos
│   ├── models.py           # Modelos de datos
│   ├── schemas.py          # Esquemas de validación
│   ├── cover_search.py     # Búsqueda de portadas
│   └── requirements.txt    # Dependencias Python
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   ├── hooks/          # Hooks personalizados
│   │   ├── contexts/       # Contextos de React
│   │   ├── LibraryView.js  # Vista principal de biblioteca
│   │   ├── UploadView.js   # Vista de carga de archivos
│   │   └── ToolsView.js    # Panel de herramientas
│   └── package.json        # Dependencias Node.js
├── docs/                   # Documentación
├── scripts/                # Scripts de automatización
└── README.md              # Este archivo
```

## 🔄 Funcionalidades de Carga

### Carga Individual
- **Arrastra y suelta** archivos PDF o EPUB
- **Selección manual** desde el explorador de archivos
- **Análisis automático** con IA para extraer metadatos
- **Extracción de portada** automática del archivo

### Carga Masiva
- **Archivos ZIP:** Sube un ZIP con múltiples libros organizados en carpetas
- **Carpetas del Sistema:** Selecciona una carpeta local para procesar todos los libros
- **Carpetas de Google Drive:** Importa libros directamente desde carpetas de Drive
- **Procesamiento Concurrente:** Hasta 4 libros procesados simultáneamente

### Detección de Duplicados
- **Verificación por nombre de archivo**
- **Comparación por título y autor**
- **Fuzzy matching** para detectar variaciones
- **Prevención automática** de duplicados

## 🖼️ Gestión de Portadas

### Extracción Automática
- **PDF:** Busca la imagen más grande en las primeras 3 páginas
- **EPUB:** Busca portada oficial, por nombre "cover", o la imagen más grande
- **Filtrado por tamaño:** Solo considera imágenes de calidad adecuada

### Búsqueda Online
- **Búsqueda individual:** Busca portada para un libro específico
- **Búsqueda masiva:** Encuentra portadas para múltiples libros
- **Fallback automático:** Si no encuentra portada, usa inicial del título

### Gestión de Archivos
- **Subida a Google Drive:** Las portadas se suben automáticamente a Drive
- **Limpieza automática:** Elimina portadas huérfanas y archivos temporales
- **URLs inteligentes:** Maneja tanto URLs locales como de Google Drive

## 🛠️ Herramientas Avanzadas

### Conversor EPUB a PDF
- **Conversión directa:** Sin necesidad de software externo
- **Apertura automática:** El PDF resultante se abre en nueva pestaña
- **Manejo de errores:** Información clara sobre problemas de conversión

### Limpieza del Sistema
- **Limpieza de archivos temporales:** Elimina archivos de procesamiento
- **Limpieza de portadas:** Elimina imágenes huérfanas
- **Optimización de base de datos:** Mantiene la integridad de los datos

### Monitoreo de Estado
- **Estado de Google Drive:** Verificación en tiempo real de la conexión
- **Información de almacenamiento:** Uso de espacio en la nube
- **Health checks:** Verificación de la salud del sistema

## 🔍 Búsqueda y Filtrado

### Búsqueda Avanzada
- **Búsqueda por título:** Encuentra libros por nombre exacto o parcial
- **Búsqueda por autor:** Localiza todos los libros de un autor
- **Búsqueda por categoría:** Filtra por género o tema
- **Búsqueda de texto completo:** Busca en cualquier campo

### Filtros Inteligentes
- **Filtro por categoría:** Muestra solo libros de una categoría específica
- **Filtro por ubicación:** Separa libros locales de los de la nube
- **Filtro por estado:** Muestra libros sincronizados o pendientes

### Paginación Optimizada
- **Configuración personalizable:** 20 libros por página por defecto
- **Navegación eficiente:** Botones de primera, anterior, siguiente y última página
- **Información de contexto:** Muestra el rango actual y total de libros

## 🎨 Interfaz de Usuario

### Modo Oscuro
- **Tema automático:** Se adapta a las preferencias del sistema
- **Cambio manual:** Botón para alternar entre modo claro y oscuro
- **Variables CSS:** Colores y estilos consistentes en toda la aplicación

### Diseño Responsivo
- **Móvil primero:** Optimizado para dispositivos móviles
- **Tablet:** Interfaz adaptada para pantallas medianas
- **Escritorio:** Experiencia completa en pantallas grandes

### Componentes Modernos
- **Lazy Loading:** Carga de imágenes optimizada
- **Skeletons:** Indicadores de carga elegantes
- **Modales:** Diálogos modernos para confirmaciones
- **Tooltips:** Información contextual en hover

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# API de Google Gemini (requerido)
GEMINI_API_KEY=tu_clave_api_aqui

# Configuración del servidor (opcional)
BACKEND_PORT=8001
FRONTEND_PORT=3000
```

### Configuración de Google Drive
- **Credenciales OAuth 2.0:** Configuración segura de autenticación
- **Permisos limitados:** Solo acceso a archivos de la aplicación
- **Tokens de acceso:** Renovación automática de permisos
- **Caché inteligente:** Optimización de consultas a la API

### Optimización de Rendimiento
- **Procesamiento concurrente:** Múltiples libros procesados simultáneamente
- **Caché de consultas:** Reducción de llamadas a APIs externas
- **Lazy loading:** Carga diferida de imágenes y componentes
- **Compresión de archivos:** Optimización de transferencia de datos

## 🚨 Solución de Problemas

### Problemas Comunes

#### Error de API de Gemini
```bash
# Verificar que la clave esté configurada
echo $GEMINI_API_KEY

# Verificar en el archivo .env
cat .env
```

#### Error de Google Drive
```bash
# Verificar configuración
python -c "from google_drive_manager import drive_manager; print('✅ OK' if drive_manager.service else '❌ Error')"

# Reconfigurar Google Drive
python setup_google_drive.py
```

#### Error de Dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt
npm install
```

### Logs y Debugging
- **Backend:** Los logs se muestran en la consola del servidor
- **Frontend:** Usa las herramientas de desarrollador del navegador
- **Google Drive:** Logs detallados en `google_drive_manager.py`

## 📊 Estadísticas y Monitoreo

### Información de Almacenamiento
- **Tamaño total:** Uso de espacio en Google Drive
- **Número de libros:** Total de libros en la biblioteca
- **Categorías:** Distribución por categorías
- **Portadas:** Estadísticas de portadas disponibles

### Rendimiento
- **Tiempo de carga:** Métricas de rendimiento de la aplicación
- **Uso de memoria:** Optimización de recursos del sistema
- **Consultas a API:** Monitoreo de uso de APIs externas

## 🔒 Seguridad

### Protección de Datos
- **Credenciales seguras:** Almacenamiento local de tokens
- **Permisos limitados:** Solo acceso necesario a Google Drive
- **Validación de entrada:** Verificación de todos los datos de entrada
- **Sanitización:** Limpieza de datos para prevenir inyecciones

### Privacidad
- **Datos locales:** La base de datos se mantiene local
- **Sin tracking:** No se recopilan datos de uso
- **Control total:** Tú tienes control completo sobre tus datos

## 📈 Roadmap

### Próximas Características
- **Sincronización bidireccional** con Google Drive
- **Etiquetas personalizadas** para organización avanzada
- **Exportación de biblioteca** en múltiples formatos
- **Análisis de lectura** y estadísticas personales
- **Integración con más servicios** de almacenamiento en la nube

### Mejoras Técnicas
- **PWA (Progressive Web App)** para instalación en dispositivos
- **Sincronización offline** con sincronización automática
- **API pública** para integración con otras aplicaciones
- **Sistema de plugins** para funcionalidades personalizadas

## 🤝 Contribución

### Cómo Contribuir
1. **Fork** el repositorio
2. Crea una **rama** para tu característica
3. **Commit** tus cambios
4. **Push** a la rama
5. Abre un **Pull Request**

### Guías de Desarrollo
- **Código limpio:** Sigue las mejores prácticas de Python y JavaScript
- **Documentación:** Documenta todas las nuevas características
- **Tests:** Añade tests para nuevas funcionalidades
- **Estilo:** Mantén consistencia con el estilo existente

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 🆘 Soporte

### Recursos de Ayuda
- **Documentación:** Consulta la carpeta `docs/` para guías detalladas
- **Issues:** Reporta problemas en el repositorio de GitHub
- **Discusiones:** Únete a las discusiones para preguntas y sugerencias

### Comunidad
- **GitHub:** [Repositorio principal](https://github.com/TU_USUARIO/TU_REPOSITORIO)
- **Issues:** [Reportar problemas](https://github.com/TU_USUARIO/TU_REPOSITORIO/issues)
- **Discussions:** [Discusiones de la comunidad](https://github.com/TU_USUARIO/TU_REPOSITORIO/discussions)

---

**¡Disfruta construyendo tu biblioteca inteligente! 📚✨**
