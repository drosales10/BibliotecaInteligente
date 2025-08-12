"""
Configuración optimizada para la API de Google Gemini
Incluye parámetros para mejorar el rendimiento y reducir rate limits
"""

import os
from typing import Dict, Any

# Configuración de la API de Gemini
GEMINI_CONFIG = {
    # Modelos
    "embedding_model": "models/text-embedding-004",
    "generation_model": "models/gemini-2.0-flash",
    
    # Parámetros de generación optimizados
    "generation_config": {
        "temperature": 0.7,  # Balance entre creatividad y precisión
        "top_p": 0.9,        # Nucleus sampling para mejor calidad
        "top_k": 40,         # Top-k sampling
        "max_output_tokens": 2048,  # Límite de tokens de salida
        "candidate_count": 1,       # Solo una respuesta por consulta
    },
    
    # Parámetros de seguridad
    "safety_settings": [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ],
    
    # Configuración de embeddings
    "embedding_config": {
        "task_type": "retrieval_document",  # Optimizado para documentos
        "title": "Book RAG Embeddings",     # Identificador del proyecto
    }
}

# Configuración de rate limiting optimizada
RATE_LIMIT_CONFIG = {
    "analysis": {
        "max_concurrent": 10,      # Llamadas concurrentes para análisis
        "max_per_minute": 60,      # 1 por segundo
        "max_per_hour": 2000,      # Límite por hora
        "retry_delay": 0.5,        # Delay base para reintentos
        "max_retries": 5,          # Máximo de reintentos
        "backoff_multiplier": 1.3  # Multiplicador de backoff
    },
    "embeddings": {
        "max_concurrent": 15,      # Llamadas concurrentes para embeddings
        "max_per_minute": 120,     # 2 por segundo
        "max_per_hour": 5000,      # Límite por hora
        "retry_delay": 0.2,        # Delay más corto para embeddings
        "max_retries": 8,          # Más reintentos para embeddings
        "backoff_multiplier": 1.1  # Backoff más suave
    }
}

# Configuración de procesamiento RAG
RAG_PROCESSING_CONFIG = {
    "chunk_size": 1000,           # Tamaño de chunk en tokens
    "chunk_overlap": 100,         # Solapamiento entre chunks
    "batch_size": 5,              # Chunks procesados por lote
    "batch_delay": 0.5,           # Delay entre lotes en segundos
    "max_chunks_per_book": 100,   # Límite de chunks por libro
    "min_chunk_length": 50,       # Longitud mínima de chunk
}

# Configuración de ChromaDB
CHROMA_CONFIG = {
    "persistence_directory": "chroma_persistence",
    "collection_name": "book_rag_collection",
    "embedding_dimension": 768,    # Dimensión de embeddings de Gemini
    "distance_function": "cosine", # Función de distancia para búsqueda
    "max_results": 10,            # Máximo de resultados por consulta
}

def get_gemini_config() -> Dict[str, Any]:
    """Obtiene la configuración completa de Gemini"""
    return GEMINI_CONFIG

def get_rate_limit_config() -> Dict[str, Any]:
    """Obtiene la configuración de rate limiting"""
    return RATE_LIMIT_CONFIG

def get_rag_config() -> Dict[str, Any]:
    """Obtiene la configuración de procesamiento RAG"""
    return RAG_PROCESSING_CONFIG

def get_chroma_config() -> Dict[str, Any]:
    """Obtiene la configuración de ChromaDB"""
    return CHROMA_CONFIG

def validate_api_key() -> bool:
    """Valida que la API key de Gemini esté configurada"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_clave_api_aqui":
        return False
    return True

def get_optimized_prompt_template(context: str, query: str, is_global: bool = False) -> str:
    """Genera un prompt optimizado para Gemini"""
    
    if is_global:
        return f"""Eres un asistente bibliotecario experto que responde preguntas basándose en el contenido de múltiples libros.

INSTRUCCIONES ESPECÍFICAS:
1. Prioriza SIEMPRE la información del Contexto proporcionado
2. Si la información del Contexto no es suficiente, puedes usar tus conocimientos generales
3. Responde SIEMPRE en español
4. Menciona de qué libros o temas proviene la información cuando sea relevante
5. Proporciona respuestas completas y bien estructuradas
6. Mantén un tono profesional pero accesible

Contexto (extraído de múltiples libros):
{context}

Pregunta: {query}

Respuesta:"""
    else:
        return f"""Eres un asistente útil que responde preguntas sobre un libro específico.
Prioriza la información del Contexto proporcionado para responder a la pregunta.
Si la información en el Contexto no es suficiente para responder la pregunta, utiliza tus conocimientos generales.
Responde siempre en español de manera clara y estructurada.

Contexto del libro:
{context}

Pregunta: {query}

Respuesta:"""
