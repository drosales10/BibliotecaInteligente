import os
import google.generativeai as genai
from dotenv import load_dotenv
import chromadb
from pypdf import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tiktoken
from rate_limiter import (
    call_gemini_embeddings_with_limit_sync,
    call_gemini_with_limit_sync,
    RateLimitExceeded
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize ChromaDB client with PERSISTENCE
# Crear directorio para persistencia de embeddings
PERSIST_DIRECTORY = "chroma_persistence"
os.makedirs(PERSIST_DIRECTORY, exist_ok=True)

print(f"🔒 ChromaDB configurado con persistencia en: {PERSIST_DIRECTORY}")

# Cliente con persistencia
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
collection = client.get_or_create_collection(name="book_rag_collection")

print(f"✅ Colección RAG cargada: {collection.name}")
print(f"📊 Total de embeddings almacenados: {collection.count()}")

# Initialize Gemini embedding model
EMBEDDING_MODEL = "models/text-embedding-004"
GENERATION_MODEL = "models/gemini-2.0-flash"

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

def chunk_text(text: str, max_tokens: int = 1000) -> list[str]:
    """Chunks text into smaller pieces based on token count."""
    if not text.strip():
        return []
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo") # Using a common tokenizer for token counting
    tokens = tokenizer.encode(text)
    chunks = []
    current_chunk_tokens = []
    for token in tokens:
        current_chunk_tokens.append(token)
        if len(current_chunk_tokens) >= max_tokens:
            chunks.append(tokenizer.decode(current_chunk_tokens))
            current_chunk_tokens = []
    if current_chunk_tokens:
        chunks.append(tokenizer.decode(current_chunk_tokens))
    return chunks

async def process_book_for_rag(file_path: str, book_id: str):
    """Extracts text, chunks it, generates embeddings, and stores in ChromaDB."""
    
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

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Could not chunk text from the book.")

    print(f"📝 Generando embeddings para {len(chunks)} chunks...")
    
    successful_chunks = 0
    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk) # No await here
            if embedding is not None: # Only add if embedding is not None
                collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{"book_id": book_id, "chunk_index": i}],
                    ids=[f"{book_id}_chunk_{i}"]
                )
                successful_chunks += 1
        except RateLimitExceeded as e:
            print(f"⚠️ Rate limit alcanzado para chunk {i}: {e}")
            # Continuar con el siguiente chunk en lugar de fallar completamente
            continue
        except Exception as e:
            print(f"❌ Error procesando chunk {i}: {e}")
            # Continuar con el siguiente chunk en lugar de fallar completamente
            continue
    
    print(f"✅ Procesado {successful_chunks}/{len(chunks)} chunks para libro ID: {book_id}")
    
    # Obtener estadísticas actualizadas
    stats = get_rag_stats()
    print(f"📊 Estadísticas RAG actualizadas: {stats}")
    
    return {"status": "processed", "chunks_processed": successful_chunks, "total_chunks": len(chunks), "stats": stats}

async def query_rag(query: str, book_id: str):
    """Queries the RAG system for answers based on the book content with rate limiting."""
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

        # Buscar chunks relevantes
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5, # Retrieve top 5 relevant chunks
            where={"book_id": book_id}
        )

        relevant_chunks = [doc for doc in results['documents'][0]]
        if not relevant_chunks:
            return "No encontré información relevante en el libro para responder tu pregunta."
            
        context = "\n\n".join(relevant_chunks)

        prompt = f"""Eres un asistente útil que responde preguntas.
Prioriza la información del Contexto proporcionado para responder a la pregunta.
Si la información en el Contexto no es suficiente para responder la pregunta, utiliza tus conocimientos generales.
Responde siempre en español.

Contexto:
{context}

Pregunta: {query}
Respuesta:"""

        # Usar rate limiter para la generación de respuesta
        def _generate_response():
            model = genai.GenerativeModel(GENERATION_MODEL)
            response = model.generate_content(prompt)
            return response.text

        return call_gemini_with_limit_sync(_generate_response)
        
    except RateLimitExceeded as e:
        return f"⚠️ El sistema está ocupado procesando otras consultas. Por favor, espera un momento e intenta de nuevo. ({e})"
    except Exception as e:
        print(f"❌ Error en consulta RAG: {e}")
        return f"❌ Ocurrió un error al procesar tu consulta: {str(e)}"

async def query_rag_global(query: str):
    """Queries the RAG system for answers based on ALL books content with rate limiting."""
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

        # Buscar chunks relevantes en TODA la base de datos (sin filtro de book_id)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,  # Más chunks para contexto global
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
        
        # Crear prompt específico para consultas globales
        prompt = f"""Eres un asistente bibliotecario experto que responde preguntas basándose en el contenido de múltiples libros.

INSTRUCCIONES ESPECÍFICAS:
1. Prioriza SIEMPRE la información del Contexto proporcionado
2. Si la información del Contexto no es suficiente, puedes usar tus conocimientos generales
3. Responde SIEMPRE en español
4. Menciona de qué libros o temas proviene la información cuando sea relevante
5. Proporciona respuestas completas y bien estructuradas

Contexto (extraído de {len(book_sources)} libros diferentes):
{context}

Pregunta: {query}

Respuesta:"""

        # Usar rate limiter para la generación de respuesta
        def _generate_response():
            model = genai.GenerativeModel(GENERATION_MODEL)
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
