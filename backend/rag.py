import os
import google.generativeai as genai
from dotenv import load_dotenv
import chromadb
from pypdf import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tiktoken
import asyncio
from rate_limiter import (
    call_gemini_embeddings_with_limit_sync,
    call_gemini_with_limit_sync,
    RateLimitExceeded
)
from gemini_config import (
    get_gemini_config,
    get_rag_config,
    get_chroma_config,
    get_optimized_prompt_template,
    validate_api_key
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validar API key
if not validate_api_key():
    print("⚠️ ADVERTENCIA: GEMINI_API_KEY no configurada o inválida")
    print("   La funcionalidad RAG estará limitada")
else:
    print("✅ GEMINI_API_KEY configurada correctamente")

genai.configure(api_key=GEMINI_API_KEY)

# Obtener configuraciones optimizadas
GEMINI_CONFIG = get_gemini_config()
RAG_CONFIG = get_rag_config()
CHROMA_CONFIG = get_chroma_config()

# Initialize ChromaDB client with PERSISTENCE
PERSIST_DIRECTORY = CHROMA_CONFIG["persistence_directory"]
os.makedirs(PERSIST_DIRECTORY, exist_ok=True)

print(f"🔒 ChromaDB configurado con persistencia en: {PERSIST_DIRECTORY}")

# Cliente con persistencia
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
collection = client.get_or_create_collection(
    name=CHROMA_CONFIG["collection_name"],
    metadata={"hnsw:space": CHROMA_CONFIG["distance_function"]}
)

print(f"✅ Colección RAG cargada: {collection.name}")
print(f"📊 Total de embeddings almacenados: {collection.count()}")

# Initialize Gemini models with optimized config
EMBEDDING_MODEL = GEMINI_CONFIG["embedding_model"]
GENERATION_MODEL = GEMINI_CONFIG["generation_model"]

def get_rag_stats():
    """Obtiene estadísticas de la base de datos RAG."""
    try:
        total_embeddings = collection.count()
        print(f"📊 Total de embeddings en la base: {total_embeddings}")
        
        # Obtener metadatos para contar libros únicos
        if total_embeddings > 0:
            # Obtener una muestra para ver metadatos
            sample = collection.get(limit=1)
            if sample and 'metadatas' in sample and sample['metadatas']:
                book_ids = set()
                for metadata in sample['metadatas']:
                    if metadata and 'book_id' in metadata:
                        book_ids.add(metadata['book_id'])
                
                return {
                    "total_embeddings": total_embeddings,
                    "unique_books": len(book_ids),
                    "persistence_directory": PERSIST_DIRECTORY,
                    "status": "active"
                }
        
        return {
            "total_embeddings": total_embeddings,
            "unique_books": 0,
            "persistence_directory": PERSIST_DIRECTORY,
            "status": "active"
        }
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas RAG: {e}")
        return {
            "total_embeddings": 0,
            "unique_books": 0,
            "persistence_directory": PERSIST_DIRECTORY,
            "status": "error",
            "error": str(e)
        }

def check_book_exists(book_id: str) -> bool:
    """Verifica si un libro ya existe en la base RAG."""
    try:
        # Buscar embeddings para este book_id
        results = collection.query(
            query_embeddings=[[0.0] * 768],  # Embedding dummy para búsqueda
            n_results=1,
            where={"book_id": book_id}
        )
        return len(results['documents'][0]) > 0
    except Exception as e:
        print(f"❌ Error verificando existencia del libro {book_id}: {e}")
        return False

def get_embedding(text):
    """Generates an embedding for the given text with rate limiting."""
    print(f"🔍 get_embedding llamado con texto: '{text}' (longitud: {len(text)})")
    if not text.strip():
        print(f"❌ Texto vacío detectado en get_embedding: '{text}'")
        return None  # Return None for empty text
    
    try:
        # Usar rate limiter para embeddings
        def _get_embedding():
            return genai.embed_content(model=EMBEDDING_MODEL, content=text)["embedding"]
        
        return call_gemini_embeddings_with_limit_sync(_get_embedding)
        
    except RateLimitExceeded as e:
        print(f"⚠️ Rate limit alcanzado para embeddings: {e}")
        raise  # Re-lanzar la excepción para manejarla apropiadamente
    except Exception as e:
        print(f"❌ Error generando embedding: {e}")
        raise  # Re-lanzar la excepción para manejarla apropiadamente

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return ""
    return text

def extract_text_from_epub(file_path: str) -> str:
    """Extracts text from an EPUB file."""
    text_content = []
    try:
        book = ebooklib.epub.read_epub(file_path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text_content.append(soup.get_text())
    except Exception as e:
        print(f"Error extracting text from EPUB {file_path}: {e}")
        return ""
    return "\n".join(text_content)

def chunk_text(text: str, max_tokens: int = None) -> list[str]:
    """Chunks text into smaller pieces based on token count with optimized settings."""
    if not text.strip():
        return []
    
    # Usar configuración optimizada si no se especifica max_tokens
    if max_tokens is None:
        max_tokens = RAG_CONFIG["chunk_size"]
    
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo") # Using a common tokenizer for token counting
    tokens = tokenizer.encode(text)
    chunks = []
    current_chunk_tokens = []
    
    for token in tokens:
        current_chunk_tokens.append(token)
        if len(current_chunk_tokens) >= max_tokens:
            chunk_text = tokenizer.decode(current_chunk_tokens)
            # Verificar longitud mínima del chunk
            if len(chunk_text.strip()) >= RAG_CONFIG["min_chunk_length"]:
                chunks.append(chunk_text)
            current_chunk_tokens = []
    
    # Agregar el último chunk si tiene contenido
    if current_chunk_tokens:
        chunk_text = tokenizer.decode(current_chunk_tokens)
        if len(chunk_text.strip()) >= RAG_CONFIG["min_chunk_length"]:
            chunks.append(chunk_text)
    
    print(f"📝 Texto dividido en {len(chunks)} chunks de máximo {max_tokens} tokens")
    return chunks

async def process_book_for_rag(file_path: str, book_id: str):
    """Extracts text, chunks it, generates embeddings, and stores in ChromaDB with optimized settings."""
    
    # Verificar si el libro ya existe en RAG
    if check_book_exists(book_id):
        print(f"✅ Libro {book_id} ya existe en RAG. Saltando reprocesamiento.")
        return {"status": "already_exists", "message": "Libro ya procesado anteriormente"}
    
    print(f"🔄 Procesando libro {book_id} para RAG...")
    
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".epub"):
        text = extract_text_from_epub(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF and EPUB are supported.")

    if not text.strip():
        raise ValueError("Could not extract text from the book.")

    # Usar configuración optimizada para chunking
    chunks = chunk_text(text, RAG_CONFIG["chunk_size"])
    if not chunks:
        raise ValueError("Could not chunk text from the book.")

    # Limitar el número de chunks por libro
    if len(chunks) > RAG_CONFIG["max_chunks_per_book"]:
        print(f"⚠️ Libro tiene {len(chunks)} chunks, limitando a {RAG_CONFIG['max_chunks_per_book']}")
        chunks = chunks[:RAG_CONFIG["max_chunks_per_book"]]

    print(f"📝 Generando embeddings para {len(chunks)} chunks...")
    
    # Procesar chunks en lotes optimizados
    batch_size = RAG_CONFIG["batch_size"]
    successful_chunks = 0
    total_chunks = len(chunks)
    
    for batch_start in range(0, total_chunks, batch_size):
        batch_end = min(batch_start + batch_size, total_chunks)
        batch_chunks = chunks[batch_start:batch_end]
        
        print(f"🔄 Procesando lote {batch_start//batch_size + 1}: chunks {batch_start+1}-{batch_end} de {total_chunks}")
        
        batch_successful = 0
        for i, chunk in enumerate(batch_chunks):
            chunk_index = batch_start + i
            try:
                embedding = get_embedding(chunk)
                if embedding is not None:
                    collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{"book_id": book_id, "chunk_index": chunk_index}],
                        ids=[f"{book_id}_chunk_{chunk_index}"]
                    )
                    successful_chunks += 1
                    batch_successful += 1
                    print(f"✅ Chunk {chunk_index + 1}/{total_chunks} procesado exitosamente")
                else:
                    print(f"⚠️ Chunk {chunk_index + 1}/{total_chunks} generó embedding nulo, saltando")
                    
            except RateLimitExceeded as e:
                print(f"⚠️ Rate limit alcanzado para chunk {chunk_index + 1}: {e}")
                # El rate limiter ya maneja reintentos automáticamente
                # Solo registrar el error y continuar
                continue
            except Exception as e:
                print(f"❌ Error procesando chunk {chunk_index + 1}: {e}")
                # Continuar con el siguiente chunk en lugar de fallar completamente
                continue
        
        print(f"📊 Lote {batch_start//batch_size + 1} completado: {batch_successful}/{len(batch_chunks)} chunks exitosos")
        
        # Pausa entre lotes usando configuración optimizada
        if batch_end < total_chunks:
            print(f"⏳ Pausa de {RAG_CONFIG['batch_delay']}s entre lotes...")
            await asyncio.sleep(RAG_CONFIG["batch_delay"])
    
    print(f"✅ Procesado {successful_chunks}/{total_chunks} chunks para libro ID: {book_id}")
    
    # Obtener estadísticas actualizadas
    stats = get_rag_stats()
    print(f"📊 Estadísticas RAG actualizadas: {stats}")
    
    return {
        "status": "processed", 
        "chunks_processed": successful_chunks, 
        "total_chunks": total_chunks, 
        "stats": stats
    }

async def query_rag(query: str, book_id: str):
    """Queries the RAG system for answers based on the book content with rate limiting and optimized prompts."""
    try:
        print(f"🔍 Consulta recibida: '{query}' (longitud: {len(query)})")
        print(f"🔍 Book ID recibido: {book_id}")
        
        # Generar embedding de la consulta con rate limiting
        try:
            query_embedding = get_embedding(query)
            print(f"🔍 Embedding generado: {len(query_embedding) if query_embedding else 0} dimensiones")
            
            if query_embedding is None:
                print(f"❌ Query vacía detectada: '{query}'")
                return "No puedo procesar una consulta vacía."
                
        except RateLimitExceeded as e:
            print(f"⚠️ Rate limit alcanzado para embedding de consulta: {e}")
            return f"⚠️ El sistema está ocupado procesando otras consultas. Por favor, espera un momento e intenta de nuevo. ({e})"

        # Buscar chunks relevantes usando configuración optimizada
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=CHROMA_CONFIG["max_results"],
            where={"book_id": book_id}
        )

        relevant_chunks = [doc for doc in results['documents'][0]]
        if not relevant_chunks:
            return "No encontré información relevante en el libro para responder tu pregunta."
            
        context = "\n\n".join(relevant_chunks)

        # Usar prompt optimizado
        prompt = get_optimized_prompt_template(context, query, is_global=False)

        # Usar rate limiter para la generación de respuesta con configuración optimizada
        def _generate_response():
            model = genai.GenerativeModel(
                GENERATION_MODEL,
                generation_config=GEMINI_CONFIG["generation_config"],
                safety_settings=GEMINI_CONFIG["safety_settings"]
            )
            response = model.generate_content(prompt)
            return response.text

        return call_gemini_with_limit_sync(_generate_response)
        
    except RateLimitExceeded as e:
        return f"⚠️ El sistema está ocupado procesando otras consultas. Por favor, espera un momento e intenta de nuevo. ({e})"
    except Exception as e:
        print(f"❌ Error en consulta RAG: {e}")
        return f"❌ Ocurrió un error al procesar tu consulta: {str(e)}"

async def query_rag_global(query: str):
    """Queries the RAG system for answers based on ALL books content with rate limiting and optimized prompts."""
    try:
        print(f"🔍 Consulta global recibida: '{query}' (longitud: {len(query)})")
        
        # Generar embedding de la consulta con rate limiting
        try:
            query_embedding = get_embedding(query)
            print(f"🔍 Embedding global generado: {len(query_embedding) if query_embedding else 0} dimensiones")
            
            if query_embedding is None:
                print(f"❌ Query vacía detectada: '{query}'")
                return "No puedo procesar una consulta vacía."
                
        except RateLimitExceeded as e:
            print(f"⚠️ Rate limit alcanzado para embedding de consulta global: {e}")
            return f"⚠️ El sistema está ocupado procesando otras consultas. Por favor, espera un momento e intenta de nuevo. ({e})"

        # Buscar chunks relevantes en TODA la base de datos usando configuración optimizada
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=CHROMA_CONFIG["max_results"] * 2,  # Más chunks para contexto global
            # Sin where clause = búsqueda en toda la colección
        )

        relevant_chunks = [doc for doc in results['documents'][0]]
        if not relevant_chunks:
            return "No encontré información relevante en ninguno de los libros para responder tu pregunta."
            
        # Obtener metadatos para identificar de qué libros provienen los chunks
        metadatas = results['metadatas'][0]
        book_sources = set()
        for metadata in metadatas:
            if metadata and 'book_id' in metadata:
                book_sources.add(metadata['book_id'])
        
        context = "\n\n".join(relevant_chunks)
        
        # Usar prompt optimizado para consultas globales
        prompt = get_optimized_prompt_template(context, query, is_global=True)

        # Usar rate limiter para la generación de respuesta con configuración optimizada
        def _generate_response():
            model = genai.GenerativeModel(
                GENERATION_MODEL,
                generation_config=GEMINI_CONFIG["generation_config"],
                safety_settings=GEMINI_CONFIG["safety_settings"]
            )
            response = model.generate_content(prompt)
            return response.text

        response_text = call_gemini_with_limit_sync(_generate_response)
        
        # Agregar información sobre las fuentes
        if book_sources:
            response_text += f"\n\n📚 **Fuentes consultadas**: Información extraída de {len(book_sources)} libros diferentes en la biblioteca."
        
        return response_text
        
    except RateLimitExceeded as e:
        return f"⚠️ El sistema está ocupado procesando otras consultas. Por favor, espera un momento e intenta de nuevo. ({e})"
    except Exception as e:
        print(f"❌ Error en consulta RAG global: {e}")
        return f"❌ Ocurrió un error al procesar tu consulta global: {str(e)}"
