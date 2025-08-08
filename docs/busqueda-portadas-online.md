# Búsqueda de Portadas Online

## Descripción

La funcionalidad de búsqueda de portadas online permite a la aplicación buscar automáticamente portadas de libros en internet cuando la extracción local falla o produce imágenes de baja calidad. Esta funcionalidad utiliza múltiples fuentes de datos para encontrar las mejores portadas disponibles.

## Características

### 🔍 Búsqueda Automática
- **Fallback automático**: Cuando la extracción de portadas del PDF/EPUB falla, la aplicación busca automáticamente portadas online
- **Información de IA**: Utiliza el título y autor extraídos por la IA para búsquedas más precisas
- **Múltiples fuentes**: Busca en OpenLibrary, Google Images, Goodreads y Amazon

### 🎯 Búsqueda Manual
- **Botón individual**: Cada libro tiene un botón 🔍 para buscar portadas online manualmente
- **Búsqueda masiva**: Botón para buscar portadas de todos los libros que no las tienen
- **Actualización automática**: Las portadas encontradas se actualizan automáticamente en la interfaz

### 📊 Validación Inteligente
- **Dimensiones mínimas**: Solo acepta imágenes de al menos 200x200 píxeles
- **Proporción correcta**: Valida que las imágenes tengan proporciones de portada de libro
- **Formato optimizado**: Convierte las imágenes a JPEG con calidad 85% para optimizar el almacenamiento

## Fuentes de Búsqueda

### 1. OpenLibrary
- **Prioridad**: Alta (primera opción)
- **Ventajas**: API gratuita, portadas de alta calidad, metadatos precisos
- **URLs**: `https://covers.openlibrary.org/b/id/{cover_id}-L.jpg`

### 2. Google Images
- **Prioridad**: Media
- **Ventajas**: Amplia cobertura, imágenes de alta resolución
- **Filtros**: Busca específicamente portadas de libros

### 3. Goodreads
- **Prioridad**: Media
- **Ventajas**: Base de datos especializada en libros
- **Acceso**: A través de búsqueda en Google Images

### 4. Amazon
- **Prioridad**: Baja
- **Ventajas**: Portadas oficiales de alta calidad
- **Acceso**: A través de búsqueda en Google Images

## Implementación Técnica

### Backend

#### Módulo `cover_search.py`
```python
class CoverSearchEngine:
    def search_openlibrary(self, title: str, author: str = None) -> Optional[str]
    def search_google_images(self, title: str, author: str = None) -> Optional[str]
    def search_goodreads(self, title: str, author: str = None) -> Optional[str]
    def search_amazon(self, title: str, author: str = None) -> Optional[str]
    def download_and_validate_image(self, image_url: str, static_dir: str, title: str, author: str = None) -> Optional[str]
    def search_book_cover(self, title: str, author: str = None, static_dir: str = "static/covers") -> Optional[str]
```

#### Endpoints API
- `POST /api/books/{book_id}/search-cover-online` - Búsqueda individual
- `POST /api/books/bulk-search-covers` - Búsqueda masiva

### Frontend

#### Componentes
- **Botón individual**: 🔍 en cada tarjeta de libro
- **Botón masivo**: "🔍 Buscar Portadas" en la barra de acciones
- **Estilos CSS**: `.search-cover-btn` y `.bulk-search-covers-btn`

#### Funciones JavaScript
```javascript
const handleSearchCoverOnline = async (book) => { /* ... */ }
const handleBulkSearchCovers = async () => { /* ... */ }
```

## Flujo de Procesamiento

### 1. Extracción Local (Primera Opción)
```
PDF/EPUB → Extraer imágenes → Validar calidad → Guardar local
```

### 2. Búsqueda Online (Fallback)
```
Sin portada → Extraer título/autor con IA → Buscar en fuentes → Descargar → Validar → Guardar
```

### 3. Validación de Imágenes
```
Descargar imagen → Verificar formato → Validar dimensiones → Verificar proporción → Guardar JPEG
```

## Configuración

### Variables de Entorno
No se requieren variables adicionales. La funcionalidad utiliza las APIs públicas disponibles.

### Dependencias
```python
requests>=2.25.1
Pillow>=8.0.0
```

## Uso

### Búsqueda Individual
1. Navegar a la biblioteca
2. Hacer clic en el botón 🔍 en cualquier libro
3. Esperar la búsqueda automática
4. La portada se actualiza automáticamente

### Búsqueda Masiva
1. Navegar a la biblioteca
2. Hacer clic en "🔍 Buscar Portadas"
3. La aplicación identifica libros sin portadas
4. Ejecuta búsquedas en paralelo
5. Muestra resultados al finalizar

## Logs y Monitoreo

### Logs del Backend
```
🔍 Buscando portada online para: 'Título del Libro' por 'Autor'
🔍 Intentando búsqueda en OpenLibrary...
✅ URL encontrada en OpenLibrary: https://covers.openlibrary.org/b/id/12345-L.jpg
✅ Portada online descargada: cover_online_Titulo_Autor_1234567890.jpg (45678 bytes)
```

### Logs del Frontend
```
Buscando portada online para: Título del Libro
Portada encontrada: cover_online_Titulo_Autor_1234567890.jpg
```

## Manejo de Errores

### Errores Comunes
- **Sin conexión**: Mensaje de error con instrucciones
- **Fuente no disponible**: Fallback a siguiente fuente
- **Imagen inválida**: Rechazo automático con validación
- **Rate limiting**: Pausas automáticas entre búsquedas

### Estrategias de Recuperación
1. **Reintentos**: Máximo 3 intentos por fuente
2. **Fallback**: Si una fuente falla, intenta la siguiente
3. **Timeout**: 10-15 segundos por búsqueda
4. **Validación**: Solo acepta imágenes válidas

## Rendimiento

### Optimizaciones
- **Búsqueda paralela**: Múltiples fuentes simultáneas
- **Cache local**: Evita descargas duplicadas
- **Compresión**: JPEG con calidad 85%
- **Validación rápida**: Rechazo temprano de imágenes inválidas

### Límites
- **Rate limiting**: 1 segundo entre búsquedas
- **Tamaño máximo**: 1MB por imagen
- **Dimensiones mínimas**: 200x200 píxeles
- **Formato**: Solo JPEG/PNG/WebP

## Casos de Uso

### Escenarios Típicos
1. **Libros escaneados**: PDFs sin portadas extraíbles
2. **EPUBs básicos**: Sin metadatos de portada
3. **Archivos corruptos**: Imágenes dañadas en el PDF
4. **Portadas de baja calidad**: Imágenes en blanco y negro o muy pequeñas

### Beneficios
- **Mejor experiencia visual**: Portadas de alta calidad
- **Identificación rápida**: Fácil reconocimiento de libros
- **Organización mejorada**: Interfaz más atractiva
- **Automatización**: Sin intervención manual requerida

## Mantenimiento

### Limpieza
- Las portadas se guardan en `static/covers/`
- Nombres únicos con timestamp
- Limpieza automática con el sistema existente

### Monitoreo
- Logs detallados para debugging
- Métricas de éxito/fallo
- Alertas para fuentes no disponibles

## Futuras Mejoras

### Funcionalidades Planificadas
- **Búsqueda por ISBN**: Mayor precisión
- **Machine Learning**: Selección automática de mejor portada
- **Más fuentes**: APIs adicionales de librerías
- **Cache distribuido**: Compartir portadas entre usuarios

### Optimizaciones
- **Búsqueda predictiva**: Anticipar portadas necesarias
- **Compresión inteligente**: Optimización automática
- **CDN**: Distribución global de portadas
