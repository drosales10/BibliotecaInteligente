# 📚 Carga Masiva de Libros

## Descripción

La funcionalidad de carga masiva permite procesar múltiples libros de forma simultánea, utilizando procesamiento concurrente y paralelo para optimizar el rendimiento.

## Características Principales

### 🔄 Procesamiento Concurrente
- **Hasta 4 libros simultáneos**: Utiliza ThreadPoolExecutor para procesar múltiples archivos en paralelo
- **Optimización de recursos**: Evita sobrecargar el sistema mientras mantiene un rendimiento óptimo
- **Manejo de errores robusto**: Cada libro se procesa de forma independiente

### 📁 Búsqueda Recursiva
- **Exploración automática**: Busca libros en todos los subdirectorios
- **Filtrado inteligente**: Procesa archivos PDF, EPUB y ZIPs que contengan libros
- **Estructura flexible**: Funciona con cualquier organización de carpetas
- **ZIPs anidados**: Procesa automáticamente ZIPs que contengan otros ZIPs con libros

### 🎯 Análisis con IA
- **Procesamiento individual**: Cada libro se analiza con Google Gemini
- **Extracción de metadatos**: Título, autor y categoría para cada libro
- **Gestión de portadas**: Extracción automática de imágenes de portada

### 🔍 Detección de Duplicados
- **Verificación por nombre de archivo**: Evita archivos con el mismo nombre
- **Verificación por título y autor**: Comparación exacta e aproximada
- **Fuzzy matching**: Detecta variaciones en títulos y autores
- **Prevención automática**: Los duplicados no se agregan a la biblioteca

## Endpoints de la API

### POST `/upload-bulk/`
Procesa un archivo ZIP que contiene libros organizados en carpetas.

**Parámetros:**
- `folder_zip`: Archivo ZIP (multipart/form-data)

**Respuesta:**
```json
{
  "message": "Procesamiento completado. X libros procesados exitosamente, Y fallaron, Z duplicados detectados.",
  "total_files": 10,
  "successful": 8,
  "failed": 1,
  "duplicates": 1,
  "successful_books": [...],
  "failed_files": [...],
  "duplicate_files": [...]
}
```

### POST `/upload-folder/`
Procesa libros desde una ruta de carpeta local (para uso administrativo).

**Parámetros:**
- `folder_path`: Ruta de la carpeta (string)

### GET `/books/health-check`
Verifica el estado de salud de los archivos de libros en la base de datos.

**Respuesta:**
```json
{
  "total_books": 10,
  "accessible_files": 8,
  "missing_files": 1,
  "orphaned_files": 1,
  "details": [
    {
      "book_id": 1,
      "title": "El Quijote",
      "file_path": "/path/to/book.pdf",
      "status": "accessible"
    }
  ]
}
```

### POST `/books/cleanup`
Ejecuta la limpieza de archivos huérfanos en el directorio de libros.

## Flujo de Procesamiento

1. **Validación de entrada**: Verifica que el archivo sea un ZIP válido
2. **Extracción**: Descomprime el archivo en un directorio temporal
3. **Búsqueda recursiva**: Encuentra todos los archivos PDF, EPUB y ZIPs
4. **Procesamiento de ZIPs anidados**: Extrae y procesa ZIPs que contengan libros
5. **Copia a directorio permanente**: Los libros extraídos de ZIPs se copian al directorio `books/`
6. **Procesamiento paralelo**: Ejecuta hasta 4 libros simultáneamente
7. **Análisis con IA**: Cada libro se analiza individualmente
8. **Verificación de duplicados**: Comprueba si el libro ya existe
9. **Almacenamiento**: Los metadatos se guardan en la base de datos (solo si no es duplicado)
10. **Limpieza**: Se eliminan los archivos temporales

## Optimizaciones Implementadas

### Concurrencia
```python
max_workers = min(4, len(book_files))  # Máximo 4 workers
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_file = {
        executor.submit(process_single_book_async, file_path, STATIC_COVERS_DIR, db): file_path
        for file_path in book_files
    }
```

### Manejo de Errores y Duplicados
- Cada libro se procesa de forma independiente
- Los errores no afectan el procesamiento de otros libros
- Se detectan y reportan duplicados automáticamente
- Se proporciona un reporte detallado de éxitos, fallos y duplicados

### Gestión de Memoria
- Uso de directorios temporales para archivos grandes
- Limpieza automática de recursos
- Procesamiento por lotes para evitar saturación

## Interfaz de Usuario

### Selector de Modo
- **Libro Individual**: Carga tradicional de un solo archivo
- **Carga Masiva**: Nueva funcionalidad para múltiples archivos

### Barra de Progreso
- Muestra el progreso del procesamiento masivo
- Información en tiempo real sobre libros procesados
- Indicadores visuales de éxito y error

### Instrucciones Claras
- Guía paso a paso para preparar el archivo ZIP
- Información sobre el procesamiento concurrente
- Expectativas de rendimiento

## Casos de Uso

### Biblioteca Personal
- Migración de colección existente
- Organización de libros por categorías
- Procesamiento de donaciones o compras masivas
- Procesamiento de libros descargados en formato ZIP
- Organización de colecciones comprimidas por autor o género

### Biblioteca Institucional
- Carga de catálogos completos
- Procesamiento de archivos históricos
- Digitalización de colecciones
- Procesamiento de archivos de respaldo comprimidos
- Migración de colecciones digitales existentes

### Desarrollo y Testing
- Carga de datos de prueba
- Validación de funcionalidades
- Optimización de rendimiento

## Consideraciones de Rendimiento

### Límites Recomendados
- **Archivos por lote**: 50-100 libros por ZIP
- **Tamaño de archivo**: Máximo 500MB por ZIP
- **Tiempo de procesamiento**: ~2-5 segundos por libro

### Factores que Afectan el Rendimiento
- **Tamaño de los archivos**: Archivos más grandes requieren más tiempo
- **Complejidad del contenido**: Textos complejos requieren más análisis de IA
- **Conectividad**: La velocidad de la API de Gemini afecta el tiempo total

## Troubleshooting

### Errores Comunes
1. **"No se encontraron archivos válidos"**: Verificar que el ZIP contenga PDF, EPUB o ZIPs con libros
2. **"Error de conexión"**: Verificar la conectividad con la API de Gemini
3. **"Tiempo de espera agotado"**: Reducir el número de archivos por lote
4. **"Duplicado detectado"**: El libro ya existe en la biblioteca (no es un error)
5. **"Error al extraer ZIP"**: Verificar que los ZIPs no estén corruptos
6. **"Archivo no encontrado en el disco"**: El archivo extraído de un ZIP no se pudo localizar

### Información sobre Duplicados
- **Por nombre de archivo**: Se detecta si ya existe un archivo con el mismo nombre
- **Por título y autor exacto**: Se detecta si ya existe un libro con el mismo título y autor
- **Por título y autor aproximado**: Se detectan variaciones en títulos y autores
- **Los duplicados no se agregan**: Se reportan pero no se procesan

### Procesamiento de ZIPs Anidados
- **Detección automática**: Se identifican ZIPs que contengan archivos PDF o EPUB
- **Extracción recursiva**: Se extraen automáticamente los libros de ZIPs anidados
- **Organización temporal**: Cada ZIP se extrae en un directorio temporal separado
- **Limpieza automática**: Los archivos temporales se eliminan después del procesamiento

### Tratamiento de Archivos Extraídos de ZIPs
- **Copia automática**: Los libros extraídos de ZIPs se copian automáticamente al directorio `books/`
- **Nombres únicos**: Se generan nombres únicos con timestamp para evitar conflictos
- **Rutas permanentes**: Las rutas en la base de datos apuntan a archivos permanentes
- **Funcionalidad completa**: Los libros extraídos de ZIPs mantienen toda la funcionalidad (descarga, lectura, etc.)
- **Verificación de integridad**: Se valida que los archivos sean accesibles antes de guardarlos

### Soluciones
- Comprimir archivos más pequeños
- Verificar la estructura del ZIP
- Revisar los logs del backend para errores específicos
- Asegurar que los ZIPs no estén protegidos con contraseña
- Verificar que los ZIPs no estén corruptos
- Usar el endpoint `/books/health-check` para diagnosticar problemas de archivos
- Ejecutar `/books/cleanup` para limpiar archivos huérfanos

## Diagnóstico y Mantenimiento

### Verificación de Salud de Archivos
El endpoint `/books/health-check` proporciona información detallada sobre:
- **Archivos accesibles**: Libros que se pueden abrir correctamente
- **Archivos faltantes**: Libros en la base de datos pero sin archivo físico
- **Archivos huérfanos**: Archivos físicos sin referencia en la base de datos

### Limpieza Automática
El endpoint `/books/cleanup` elimina archivos huérfanos que pueden acumularse por:
- Procesamiento interrumpido de ZIPs
- Eliminación manual de archivos
- Errores durante la carga masiva

## Próximas Mejoras

- [ ] Procesamiento asíncrono con colas
- [ ] Interfaz de monitoreo en tiempo real
- [ ] Configuración personalizable de concurrencia
- [ ] Soporte para más formatos de archivo
- [ ] Integración con servicios de almacenamiento en la nube

## Ejemplos de Uso y Testing

### Estructura de ZIP de Prueba
```
test_books.zip
├── libros_directos/
│   ├── libro1.pdf
│   └── libro2.epub
├── colecciones/
│   ├── autor1.zip
│   │   ├── libro3.pdf
│   │   └── libro4.epub
│   └── autor2.zip
│       └── libro5.pdf
└── miscelaneos/
    └── otros.zip
        └── libro6.epub
```

### Verificación Post-Carga
1. **Cargar ZIP**: Usar el endpoint `/upload-bulk/`
2. **Verificar salud**: GET `/books/health-check`
3. **Probar descarga**: GET `/books/download/{book_id}`
4. **Limpiar huérfanos**: POST `/books/cleanup`

### Casos de Prueba
- **ZIP simple**: Contiene solo archivos PDF/EPUB
- **ZIP anidado**: Contiene otros ZIPs con libros
- **ZIP mixto**: Combina archivos directos y ZIPs anidados
- **ZIP con duplicados**: Para probar detección de duplicados
- **ZIP corrupto**: Para probar manejo de errores 