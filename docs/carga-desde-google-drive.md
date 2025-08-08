# Carga de Libros desde Google Drive

## 🎯 **Funcionalidad Implementada**

Se ha implementado la funcionalidad para cargar libros desde carpetas públicas de Google Drive en modo nube, siguiendo las mismas pautas que la carga por carpeta local pero adaptada para el almacenamiento en la nube.

## ✨ **Características Principales**

### **1. Búsqueda Recursiva**
- ✅ Explora recursivamente todos los subdirectorios de la carpeta seleccionada
- ✅ Procesa archivos PDF y EPUB encontrados en cualquier nivel de profundidad
- ✅ Ignora archivos que no son libros válidos

### **2. Organización Automática**
- ✅ Crea carpetas por categorías automáticamente
- ✅ Organiza libros por letras (A-Z) dentro de cada categoría
- ✅ Las portadas se guardan en la carpeta `@covers` de Google Drive

### **3. Procesamiento Inteligente**
- ✅ Análisis con IA para extraer metadatos (título, autor, categoría)
- ✅ Detección automática de duplicados
- ✅ Procesamiento secuencial para evitar límites de tamaño

## 🔧 **Implementación Técnica**

### **Backend**

#### **Google Drive Manager (`backend/google_drive_manager.py`)**
```python
# Nuevas funciones agregadas:

def extract_folder_id_from_url(self, drive_url):
    """Extrae el ID de carpeta de una URL pública de Google Drive"""

def list_public_folder_contents(self, folder_url):
    """Lista el contenido de una carpeta pública de Google Drive"""

def download_file_from_drive(self, file_id, temp_dir):
    """Descarga un archivo desde Google Drive a un directorio temporal"""

def process_public_folder_recursively(self, folder_url, temp_dir):
    """Procesa recursivamente una carpeta pública de Google Drive"""

def is_valid_book_file(self, filename):
    """Verifica si un archivo es un libro válido (PDF o EPUB)"""
```

#### **Endpoint (`backend/main.py`)**
```python
@app.post("/api/upload-drive-folder/", response_model=schemas.BulkUploadResponse)
async def upload_drive_folder_books(folder_data: dict, db: Session = Depends(get_db)):
    """Carga masiva de libros desde una carpeta pública de Google Drive (MODO NUBE)"""
```

### **Frontend**

#### **UploadView (`frontend/src/UploadView.js`)**
- ✅ Nuevo modo de carga: `drive-folder`
- ✅ Campo de entrada para URL de Google Drive
- ✅ Validación de formato de URL
- ✅ Manejo de errores específicos para Google Drive
- ✅ Progreso detallado del procesamiento

## 📋 **Flujo de Procesamiento**

### **1. Validación de Entrada**
- Verifica que la URL sea de Google Drive
- Extrae el ID de carpeta de la URL
- Valida que la carpeta sea accesible

### **2. Exploración Recursiva**
- Lista contenido de la carpeta raíz
- Explora subdirectorios recursivamente
- Filtra solo archivos PDF y EPUB

### **3. Descarga y Procesamiento**
- Descarga cada archivo a directorio temporal
- Procesa con IA para extraer metadatos
- Verifica duplicados
- Sube a Google Drive organizado

### **4. Limpieza**
- Elimina archivos temporales
- Actualiza base de datos
- Devuelve resumen de resultados

## 🔗 **Formatos de URL Soportados**

La funcionalidad soporta los siguientes formatos de URL de Google Drive:

1. **Carpeta directa:**
   ```
   https://drive.google.com/drive/folders/[ID]
   ```

2. **URL de apertura:**
   ```
   https://drive.google.com/open?id=[ID]
   ```

3. **Archivo individual:**
   ```
   https://drive.google.com/file/d/[ID]/view
   ```

## 🎨 **Interfaz de Usuario**

### **Selector de Modo**
- Nuevo botón "💾 Google Drive" en el selector de modo
- Solo disponible en modo nube
- Interfaz consistente con otros modos

### **Campo de Entrada**
- Campo de texto para URL de Google Drive
- Placeholder con ejemplo de formato
- Validación en tiempo real

### **Ayuda Contextual**
- Modal de ayuda específico para Google Drive
- Instrucciones detalladas
- Formatos de URL soportados

## ⚙️ **Configuración Requerida**

### **Google Drive API**
- ✅ Credenciales configuradas (`credentials.json`)
- ✅ Token de acceso válido (`token.json`)
- ✅ Permisos de lectura en carpetas públicas

### **Backend**
- ✅ Google Drive Manager inicializado
- ✅ Conexión a Google Drive API establecida
- ✅ Carpeta raíz configurada

## 🚀 **Uso**

### **1. Seleccionar Modo**
- Cambiar a modo nube
- Seleccionar "💾 Google Drive"

### **2. Ingresar URL**
- Copiar URL de carpeta pública de Google Drive
- Pegar en el campo de entrada
- Verificar formato

### **3. Iniciar Procesamiento**
- Hacer clic en "Analizar y Guardar Libros de Google Drive"
- Esperar procesamiento
- Revisar resultados

## 📊 **Resultados**

### **Respuesta del Servidor**
```json
{
  "message": "Procesamiento completado. X libros procesados exitosamente, Y fallaron, Z duplicados detectados.",
  "total_files": 25,
  "successful": 20,
  "failed": 3,
  "duplicates": 2,
  "successful_books": [...],
  "failed_files": [...],
  "duplicate_files": [...]
}
```

### **Organización en Google Drive**
```
📁 Biblioteca Inteligente/
├── 📁 Ficción/
│   ├── 📁 A/
│   ├── 📁 B/
│   └── ...
├── 📁 No Ficción/
│   ├── 📁 A/
│   ├── 📁 B/
│   └── ...
└── 📁 @covers/
    ├── cover_libro1_autor1_timestamp.png
    └── ...
```

## 🔍 **Logging y Debugging**

### **Logs del Backend**
- ✅ Progreso de exploración recursiva
- ✅ Archivos encontrados y procesados
- ✅ Errores de descarga y procesamiento
- ✅ Resumen final de resultados

### **Logs del Frontend**
- ✅ Estado de conexión con backend
- ✅ Progreso de procesamiento
- ✅ Errores específicos de Google Drive

## 🛡️ **Manejo de Errores**

### **Errores Comunes**
1. **URL inválida:** Formato no reconocido
2. **Carpeta inaccesible:** Permisos insuficientes
3. **Google Drive no configurado:** Credenciales faltantes
4. **Timeout:** Carpeta muy grande o conexión lenta
5. **Archivos corruptos:** Error en descarga

### **Recuperación**
- ✅ Reintentos automáticos para errores temporales
- ✅ Limpieza de archivos temporales
- ✅ Mensajes de error descriptivos
- ✅ Logs detallados para debugging

## 🔄 **Compatibilidad**

### **Modos de Aplicación**
- ✅ **Modo Nube:** Funcionalidad completa
- ❌ **Modo Local:** No disponible (por diseño)

### **Navegadores**
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge

## 📈 **Rendimiento**

### **Optimizaciones**
- ✅ Procesamiento secuencial para evitar rate limiting
- ✅ Descarga temporal para procesamiento local
- ✅ Limpieza automática de archivos temporales
- ✅ Timeout configurable (15 minutos)

### **Límites**
- Tamaño máximo de archivo: Según límites de Google Drive
- Número de archivos: Sin límite práctico
- Tiempo de procesamiento: Depende del número y tamaño de archivos

## 🎯 **Próximas Mejoras**

### **Funcionalidades Futuras**
- [ ] Procesamiento paralelo con límites configurables
- [ ] Resumen de progreso en tiempo real
- [ ] Cancelación de procesamiento
- [ ] Filtros por tipo de archivo
- [ ] Validación previa de carpetas

### **Optimizaciones**
- [ ] Caché de metadatos de carpetas
- [ ] Compresión de archivos temporales
- [ ] Procesamiento incremental
- [ ] Métricas de rendimiento

## ✅ **Estado Actual**

La funcionalidad está **completamente implementada** y lista para uso en producción con las siguientes características:

- ✅ Búsqueda recursiva en carpetas públicas de Google Drive
- ✅ Organización automática por categorías y letras
- ✅ Almacenamiento de portadas en @covers
- ✅ Detección de duplicados
- ✅ Interfaz de usuario completa
- ✅ Manejo robusto de errores
- ✅ Documentación completa
