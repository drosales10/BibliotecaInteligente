# 🚀 Configuración de Google Drive para Biblioteca Inteligente

Este documento te guiará a través del proceso de configuración de Google Drive para almacenar libros organizados por categorías y orden alfabético.

## ⚠️ IMPORTANTE: Almacenamiento Exclusivo en la Nube

**La aplicación ahora funciona exclusivamente con Google Drive.** Los libros ya no se almacenan localmente, lo que significa:

- ✅ **Ahorro de espacio en disco**: Los archivos no ocupan espacio local
- ✅ **Acceso desde cualquier lugar**: Los libros están disponibles en la nube
- ✅ **Organización automática**: Estructura por categorías y letras A-Z
- ✅ **Sincronización automática**: Todos los cambios se reflejan en Drive

## 📋 Requisitos Previos

- Cuenta de Google
- Acceso a Google Cloud Console
- Python 3.7 o superior
- Dependencias instaladas (ver requirements.txt)

## 🔧 Pasos de Configuración

### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el ID del proyecto

### 2. Habilitar Google Drive API

1. En la consola, ve a "APIs y servicios" > "Biblioteca"
2. Busca "Google Drive API"
3. Haz clic en "Habilitar"

### 3. Crear Credenciales OAuth 2.0

1. Ve a "APIs y servicios" > "Credenciales"
2. Haz clic en "Crear credenciales" > "ID de cliente de OAuth 2.0"
3. Selecciona "Aplicación de escritorio"
4. Dale un nombre descriptivo (ej: "Biblioteca Inteligente")
5. Haz clic en "Crear"

### 4. Descargar Credenciales

1. En la lista de credenciales, haz clic en el ID de cliente que creaste
2. Haz clic en "Descargar JSON"
3. Renombra el archivo a `credentials.json`
4. Coloca el archivo en la carpeta `backend/`

### 5. Ejecutar Script de Configuración

```bash
cd backend
python setup_google_drive.py
```

El script te guiará a través del proceso de autorización y configuración.

## 📁 Estructura de Organización

Los libros se organizarán automáticamente en Google Drive de la siguiente manera:

```
Biblioteca Inteligente/
├── Psicología/
│   ├── A/
│   │   ├── Libro1.pdf
│   │   └── Libro2.pdf
│   ├── B/
│   │   └── Libro3.pdf
│   └── C/
│       └── Libro4.pdf
├── Filosofía/
│   ├── A/
│   └── B/
└── Ciencia/
    ├── A/
    └── B/
```

### Reglas de Organización

- **Categorías**: Se crean automáticamente basadas en el análisis de IA
- **Letras A-Z**: Se basan en la primera letra significativa del título (ignorando artículos)
- **Artículos ignorados**: "El", "La", "Los", "Las", "Un", "Una", "The", "A", "An"

## 🔄 Migración de Datos Existentes

Si ya tienes libros en la aplicación, puedes migrarlos a Google Drive:

### Migración Automática (Recomendado)

```bash
cd backend
python migrate_to_drive.py
```

Este script:
- Sube todos los libros existentes a Google Drive
- Actualiza la base de datos con los IDs de Drive
- Mantiene los archivos locales como respaldo

### Migración a Almacenamiento Exclusivo en la Nube

```bash
cd backend
python migrate_to_cloud_only.py
```

Este script:
- Verifica que todos los libros estén en Google Drive
- Elimina todos los archivos locales
- Actualiza la base de datos para funcionar solo con Drive

## 🔍 Verificación de Configuración

### Verificar Conexión

```bash
python -c "from google_drive_manager import drive_manager; print('✅ Conexión exitosa' if drive_manager.service else '❌ Error de conexión')"
```

### Verificar Estructura

```bash
python -c "from google_drive_manager import drive_manager; info = drive_manager.get_storage_info(); print(f'Carpeta: {info[\"root_folder_name\"]}, Tamaño: {info[\"total_size_mb\"]} MB')"
```

### Verificar Estado de la Aplicación

```bash
python migrate_to_cloud_only.py
# Selecciona opción 1 para ver el estado actual
```

## 🚨 Solución de Problemas

### Error: "Archivo credentials.json no encontrado"

**Solución**: Asegúrate de que el archivo `credentials.json` esté en la carpeta `backend/`

### Error: "Error al inicializar Google Drive"

**Solución**: 
1. Verifica que la API de Google Drive esté habilitada
2. Asegúrate de que las credenciales sean correctas
3. Revisa los permisos del proyecto

### Error: "Quota exceeded"

**Solución**: 
1. Verifica el uso de cuota en Google Cloud Console
2. Considera actualizar a un plan de pago si es necesario

### Error: "Google Drive no está configurado"

**Solución**:
1. Ejecuta `python setup_google_drive.py`
2. Sigue las instrucciones de configuración
3. Verifica que el archivo `token.json` se haya creado

## 📊 Monitoreo de Uso

### Información de Almacenamiento

```python
from google_drive_manager import drive_manager

# Obtener información de uso
info = drive_manager.get_storage_info()
print(f"Tamaño total: {info['total_size_gb']} GB")
```

### Listar Libros por Categoría

```python
# Listar todos los libros de Psicología
books = drive_manager.list_books_by_category("Psicología")
for book in books:
    print(f"- {book['name']}")
```

## 🔒 Seguridad

- Las credenciales se almacenan localmente en `token.json`
- Nunca compartas los archivos `credentials.json` o `token.json`
- Usa `.gitignore` para excluir estos archivos del control de versiones

## 📈 Funcionalidades

Una vez configurado Google Drive:

1. **Carga Individual**: Los libros se suben directamente a Drive
2. **Carga Masiva**: ZIPs y carpetas se procesan y suben a Drive
3. **Descarga**: Los libros se descargan temporalmente desde Drive
4. **Eliminación**: Los libros se eliminan tanto de Drive como de la base de datos
5. **Organización**: Estructura automática por categorías y letras

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en la consola
2. Verifica la configuración de Google Cloud Console
3. Asegúrate de que todas las dependencias estén instaladas
4. Consulta la documentación oficial de Google Drive API

---

**¡Listo!** Tu biblioteca ahora funciona exclusivamente con Google Drive, ahorrando espacio local y proporcionando acceso desde cualquier lugar. 🎉 