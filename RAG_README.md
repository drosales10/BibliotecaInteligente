# 🤖 Sistema RAG (Retrieval-Augmented Generation)

## 📋 Descripción

El sistema RAG permite conversar con libros usando inteligencia artificial. Los libros se procesan para crear embeddings vectoriales que se almacenan de forma persistente, permitiendo consultas inteligentes sobre su contenido.

## 🔒 **PERSISTENCIA IMPLEMENTADA**

### ✅ **Antes (SIN persistencia)**
- ❌ Embeddings se perdían al recargar la página
- ❌ Embeddings se perdían al reiniciar el servidor
- ❌ Reprocesamiento completo de libros cada vez
- ❌ Costos innecesarios en llamadas a API
- ❌ Tiempo perdido reprocesando libros

### ✅ **Ahora (CON persistencia)**
- ✅ Embeddings se mantienen entre sesiones
- ✅ Embeddings se mantienen al reiniciar servidor
- ✅ No reprocesamiento de libros existentes
- ✅ Ahorro de costos y tiempo
- ✅ Base de datos vectorial persistente

## 🏗️ **Arquitectura del Sistema**

### **Backend (Python/FastAPI)**
```
backend/
├── rag.py                    # Módulo principal RAG
├── main.py                   # Endpoints de la API
├── chroma_persistence/       # Directorio de persistencia
│   ├── chroma.sqlite3       # Base de datos SQLite
│   ├── embeddings/          # Archivos de embeddings
│   └── collections/         # Metadatos de colecciones
└── requirements.txt          # Dependencias
```

### **Frontend (React)**
```
frontend/src/
├── RagView.js               # Componente principal RAG
├── RagView.css              # Estilos del componente
└── config/api.js            # Configuración de API
```

## 🚀 **Endpoints Disponibles**

### **POST** `/rag/upload-book/`
Sube un libro para procesamiento RAG
```json
{
  "book_id": "uuid",
  "message": "Libro procesado exitosamente"
}
```

### **POST** `/rag/query/`
Consulta la IA sobre el contenido de un libro
```json
{
  "query": "¿De qué trata este libro?",
  "book_id": "uuid"
}
```

### **GET** `/rag/status`
Obtiene estadísticas del sistema RAG
```json
{
  "status": "success",
  "rag_stats": {
    "total_embeddings": 150,
    "unique_books": 3,
    "persistence_directory": "chroma_persistence",
    "status": "active"
  }
}
```

### **DELETE** `/rag/book/{book_id}`
Elimina un libro y sus embeddings de RAG

## 🔧 **Configuración**

### **Variables de Entorno**
```bash
# .env
GEMINI_API_KEY=tu_api_key_de_gemini
```

### **Dependencias Python**
```txt
# requirements.txt
chromadb
google-generativeai
pypdf
ebooklib
beautifulsoup4
tiktoken
```

## 📊 **Flujo de Trabajo**

### **1. Carga de Libro**
```
Libro PDF/EPUB → Extracción de texto → Chunking → Embeddings → ChromaDB
```

### **2. Consulta RAG**
```
Pregunta → Embedding de consulta → Búsqueda vectorial → Contexto → Respuesta IA
```

### **3. Persistencia**
```
ChromaDB PersistentClient → Directorio local → SQLite + archivos binarios
```

## 🧪 **Pruebas de Persistencia**

### **Script de Prueba**
```bash
python test_rag_persistence.py
```

### **Verificación Manual**
1. Ejecuta el script de prueba
2. Reinicia el servidor backend
3. Ejecuta el script nuevamente
4. Los embeddings deberían mantenerse

## 🎯 **Características del Sistema**

### **✅ Implementado**
- [x] Persistencia de embeddings en ChromaDB
- [x] Detección de libros duplicados
- [x] Procesamiento de PDF y EPUB
- [x] Chunking inteligente de texto
- [x] Embeddings con Google Gemini
- [x] Búsqueda vectorial semántica
- [x] Interfaz web moderna
- [x] Soporte para modo oscuro
- [x] Estadísticas en tiempo real
- [x] Endpoints REST completos

### **🔮 Futuras Mejoras**
- [ ] Compresión de embeddings
- [ ] Backup automático de base vectorial
- [ ] Búsqueda semántica avanzada
- [ ] Clustering de documentos similares
- [ ] Análisis de sentimientos
- [ ] Resúmenes automáticos

## 🚨 **Solución al Problema de Persistencia**

### **Problema Identificado**
```python
# ❌ ANTES: Sin persistencia
client = chromadb.Client()  # Cliente en memoria
```

### **Solución Implementada**
```python
# ✅ AHORA: Con persistencia
PERSIST_DIRECTORY = "chroma_persistence"
os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
```

### **Beneficios de la Solución**
1. **Persistencia Total**: Los embeddings se mantienen entre sesiones
2. **Ahorro de Costos**: No reprocesamiento de libros existentes
3. **Mejor UX**: Respuestas instantáneas para libros ya procesados
4. **Escalabilidad**: Base de datos vectorial que crece con el tiempo
5. **Confiabilidad**: Datos protegidos contra pérdidas

## 🔍 **Monitoreo y Debugging**

### **Logs del Sistema**
```python
print(f"🔒 ChromaDB configurado con persistencia en: {PERSIST_DIRECTORY}")
print(f"✅ Colección RAG cargada: {collection.name}")
print(f"📊 Total de embeddings almacenados: {collection.count()}")
```

### **Estadísticas en Tiempo Real**
- Total de embeddings almacenados
- Número de libros únicos procesados
- Estado del sistema (activo/error)
- Directorio de persistencia utilizado

## 🛠️ **Mantenimiento**

### **Limpieza de Datos**
```bash
# Eliminar libro específico
DELETE /rag/book/{book_id}

# Verificar estado
GET /rag/status
```

### **Backup de Base Vectorial**
```bash
# El directorio chroma_persistence/ contiene toda la información
# Copiar este directorio para hacer backup
cp -r chroma_persistence/ backup_rag_$(date +%Y%m%d)/
```

## 📱 **Compatibilidad con Tailscale**

### **✅ Totalmente Compatible**
- Persistencia local funciona en cualquier red
- Embeddings se mantienen independientemente del acceso
- Sistema funciona en modo LOCAL, WIFI y TAILSCALE
- Base vectorial accesible desde cualquier dispositivo

### **🔒 Seguridad**
- Datos almacenados localmente en el servidor
- No hay transferencia de embeddings a servicios externos
- Solo se envían consultas y respuestas por la red
- Certificados SSL para comunicación segura

---

## 🎉 **Conclusión**

El sistema RAG ahora tiene **persistencia completa** que resuelve todos los problemas anteriores:

- ✅ **NO más pérdida de embeddings**
- ✅ **NO más reprocesamiento innecesario**
- ✅ **SÍ ahorro de costos y tiempo**
- ✅ **SÍ mejor experiencia de usuario**
- ✅ **SÍ escalabilidad a largo plazo**

**¡Tu biblioteca inteligente ahora es verdaderamente persistente!** 🚀
