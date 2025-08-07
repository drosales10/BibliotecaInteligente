# Funcionalidad de Selección de Carpeta

## Descripción

La funcionalidad de selección de carpeta permite a los usuarios cargar múltiples libros de forma recursiva desde una carpeta local de su computadora. Esta función está disponible **exclusivamente en modo local**.

## Características

### ✅ Funcionalidades Implementadas

1. **Selección de Carpeta**: Utiliza la API `window.showDirectoryPicker()` del navegador para permitir al usuario seleccionar una carpeta.

2. **Exploración Recursiva**: Busca automáticamente en todos los subdirectorios de la carpeta seleccionada.

3. **Filtrado de Archivos**: Solo procesa archivos PDF y EPUB, ignorando otros tipos de archivo.

4. **Procesamiento Secuencial**: Los archivos se procesan uno por uno para evitar límites de tamaño del navegador.

5. **Modo Local Exclusivo**: Solo funciona cuando la aplicación está en modo local.

6. **Logging Detallado**: Proporciona información detallada en la consola del navegador durante el proceso.

7. **Manejo de Errores**: Incluye manejo robusto de errores y cancelaciones del usuario.

8. **Barra de Progreso**: Muestra el progreso del procesamiento en tiempo real.

## Flujo de Funcionamiento

### 1. Selección de Carpeta
```javascript
const dirHandle = await window.showDirectoryPicker();
```

### 2. Exploración Recursiva
```javascript
const collectFiles = async (handle, depth = 0) => {
  for await (const entry of handle.values()) {
    if (entry.kind === 'file') {
      // Procesar archivo
    } else if (entry.kind === 'directory') {
      // Explorar subdirectorio
      await collectFiles(entry, depth + 1);
    }
  }
};
```

### 3. Filtrado de Archivos
- Solo archivos con extensión `.pdf` o `.epub`
- Se ignoran archivos ZIP y otros tipos

### 4. Procesamiento Individual
- Cada archivo se envía al endpoint `/api/upload-book-local/`
- Se utiliza el hook `useBookService.uploadBook()`
- Se manejan duplicados y errores individualmente

## Restricciones

### Navegador
- Requiere un navegador moderno que soporte la API `showDirectoryPicker()`
- Compatible con Chrome 86+, Edge 86+, Firefox 111+

### Modo de Aplicación
- **Solo disponible en modo local**
- No funciona en modo nube (Google Drive)

### Tipos de Archivo
- Solo archivos PDF y EPUB
- No procesa archivos ZIP (usar la opción de carga masiva para ZIPs)

## Interfaz de Usuario

### Modo Local
- Botón "📁 Seleccionar Carpeta" habilitado
- Instrucciones específicas para modo local
- Barra de progreso durante el procesamiento

### Modo Nube
- Botón deshabilitado
- Mensaje de advertencia explicando que solo está disponible en modo local

## Logging y Debugging

### Consola del Navegador
```javascript
🔍 Iniciando selección de carpeta...
✅ Carpeta seleccionada: MiBiblioteca
🔍 Iniciando procesamiento de archivos de carpeta: MiBiblioteca
📁 Explorando: MiBiblioteca
  📄 Archivo encontrado: libro1.pdf (1024000 bytes)
  ✅ Archivo válido agregado: libro1.pdf
  📁 Subdirectorio encontrado: subcarpeta
    📄 Archivo encontrado: libro2.epub (2048000 bytes)
    ✅ Archivo válido agregado: libro2.epub
✅ Total de archivos válidos encontrados: 2
```

### Mensajes de Estado
- ✅ Éxito: "Carpeta seleccionada: [nombre]"
- ❌ Error: "Tu navegador no soporta la selección de carpetas"
- ⚠️ Cancelación: "Selección de carpeta cancelada por el usuario"

## Mejoras Implementadas

### 1. Verificación de Modo
```javascript
if (appMode !== 'local') {
  setMessage('❌ La selección de carpeta solo está disponible en modo local.');
  return;
}
```

### 2. Logging Detallado
- Información de cada archivo encontrado
- Progreso del procesamiento
- Errores específicos por archivo

### 3. Manejo de Errores Mejorado
- Distinción entre cancelación del usuario y errores reales
- Mensajes específicos para cada tipo de error

### 4. Interfaz Condicional
- Muestra advertencia cuando no está en modo local
- Botón deshabilitado cuando no es aplicable

## Endpoints del Backend

### Carga Individual Local
```
POST /api/upload-book-local/
```

### Parámetros
- `book_file`: Archivo PDF o EPUB

### Respuesta
```json
{
  "id": 123,
  "title": "Título del Libro",
  "author": "Autor del Libro",
  "category": "Categoría",
  "cover_image_url": "cover_filename.png",
  "file_path": "/path/to/local/file.pdf"
}
```

## Estado Actual

✅ **FUNCIONALIDAD COMPLETA**

- Selección de carpeta funciona correctamente
- Exploración recursiva implementada
- Procesamiento en modo local funcional
- Interfaz de usuario mejorada
- Logging detallado implementado
- Manejo de errores robusto

## Próximos Pasos

1. **Testing**: Probar con diferentes estructuras de carpetas
2. **Performance**: Optimizar para carpetas con muchos archivos
3. **UX**: Considerar indicadores visuales adicionales
4. **Error Handling**: Agregar más casos específicos de error 