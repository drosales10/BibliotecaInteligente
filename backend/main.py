from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
import io
import fitz
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import List
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import zipfile
from pathlib import Path
import time
import threading
import uuid
from googleapiclient.http import MediaIoBaseDownload
import hashlib

import crud, models, database, schemas
import cover_search
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuración Inicial ---
load_dotenv(dotenv_path='../.env')
API_KEY = os.getenv("GEMINI_API_KEY")
print(f"🔑 Clave de API cargada: {API_KEY[:10]}..." if API_KEY else "❌ No se encontró la clave de API")
if not API_KEY: 
    print("⚠️  ADVERTENCIA: No se encontró la GEMINI_API_KEY. La funcionalidad de IA estará limitada.")
    API_KEY = "dummy_key"  # Clave temporal para evitar errores
genai.configure(api_key=API_KEY)
models.Base.metadata.create_all(bind=database.engine)

# Semáforo para limitar llamadas concurrentes a la API de IA
ai_semaphore = threading.Semaphore(2)  # Máximo 2 llamadas concurrentes a la IA

# --- Funciones de IA y Procesamiento ---
def analyze_with_gemini(text: str, max_retries: int = 3) -> dict:
    """
    Analiza texto con Gemini AI con manejo robusto de errores y retry logic
    """
    # Usar semáforo para limitar llamadas concurrentes
    with ai_semaphore:
        model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Eres un bibliotecario experto. Analiza el siguiente texto extraído de las primeras páginas de un libro.
    Tu tarea es identificar el título, el autor y la categoría principal del libro.
    
    INSTRUCCIONES ESPECÍFICAS:
    1. Para el TÍTULO: Busca el título principal del libro, generalmente en mayúsculas o al inicio del texto. El título debe guardarse en la base de datos en formato capitalizado, nunca todo en mayúsculas.
    2. Para el AUTOR: Busca el nombre del autor, que suele aparecer después de "por", "de", "autor:", o en la portada, también puede estar en el nombre del mismo archivo
    3. Para la CATEGORÍA: Determina el género o categoría principal SIEMPRE EN ESPAÑOL (ej: Psicología, Literatura, Ciencia, Historia, Tecnología, Medicina, etc.)
    4. Para la categoria te puedes guiar por el nombre de la ruta del libro, por ejemplo: "Psicología/Psicología General/Psicología Clínica"
    5. IMPORTANTE: La categoría DEBE estar siempre en español, nunca en inglés
    
    CATEGORÍAS COMUNES EN ESPAÑOL:
    - Psicología, Literatura, Ciencia, Historia, Tecnología, Medicina, Filosofía, Economía, Política, Arte, Música, Deportes, Cocina, Viajes, Biografía, Autoayuda, Religión, Educación, Derecho, Marketing, Administración, Contabilidad, Ingeniería, Arquitectura, Diseño, Fotografía, Cine, Teatro, Danza, Moda, Jardinería, Manualidades, etc.
    
    Devuelve ÚNICAMENTE un objeto JSON con las claves "title", "author" y "category".
    Si no puedes determinar un valor específico, usa "Desconocido".
    
    Ejemplo: {{'title': 'El nombre del viento', 'author': 'Patrick Rothfuss', 'category': 'Fantasía'}}
    
    Texto a analizar: --- {text[:4000]} ---
    """
    
    for attempt in range(max_retries):
        try:
            # Configurar timeout y parámetros de seguridad
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Menor temperatura para respuestas más consistentes
                    max_output_tokens=500,  # Limitar tokens de salida
                    top_p=0.8,
                    top_k=40
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            )
            
            match = response.text.strip()
            print(f"Respuesta original de la IA: {match}")
            
            if match.startswith("```json"):
                match = match[7:]
            if match.endswith("```"):
                match = match[:-3]
            
            print(f"Respuesta procesada: {match}")
            result = json.loads(match.strip())
            print(f"Resultado parseado: {result}")
            
            # Validar que el resultado tenga las claves esperadas
            if not all(key in result for key in ["title", "author", "category"]):
                raise ValueError("Respuesta de IA incompleta")
            
            # Traducir la categoría a español si es necesario
            if "category" in result and result["category"]:
                result["category"] = translate_category_to_spanish(result["category"])
            
            # Si la IA devuelve "Desconocido", mantenerlo (no es un error)
            # Solo cambiar si realmente hay un error en el procesamiento
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error de JSON en intento {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {"title": "Título no detectado", "author": "Autor no detectado", "category": "Sin categoría"}
            time.sleep(1)  # Esperar antes del retry
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"Error de IA en intento {attempt + 1}: {e}")
            print(f"Tipo de error: {type(e).__name__}")
            
            # Si es un error de rate limiting o quota, esperar más tiempo
            if any(keyword in error_msg for keyword in ["quota", "rate", "limit", "too many", "429", "resource exhausted"]):
                wait_time = (attempt + 1) * 3  # Espera progresiva: 3s, 6s, 9s
                print(f"Rate limit detectado, esperando {wait_time} segundos...")
                time.sleep(wait_time)
            elif "timeout" in error_msg or "deadline" in error_msg:
                wait_time = (attempt + 1) * 2
                print(f"Timeout detectado, esperando {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                time.sleep(1)  # Espera corta para otros errores
            
            if attempt == max_retries - 1:
                print(f"Error final después de {max_retries} intentos: {e}")
                return {"title": "Título no detectado", "author": "Autor no detectado", "category": "Sin categoría"}
    
    return {"title": "Título no detectado", "author": "Autor no detectado", "category": "Sin categoría"}

def process_pdf(file_path: str, static_dir: str) -> dict:
    doc = fitz.open(file_path)
    text = ""
    
    # Extraer texto de más páginas para mejor análisis
    max_pages = min(len(doc), 10)  # Aumentar de 5 a 10 páginas
    for i in range(max_pages): 
        text += doc.load_page(i).get_text("text", sort=True)
    
    # Agregar información de depuración
    print(f"📄 PDF procesado: {os.path.basename(file_path)}")
    print(f"📄 Páginas extraídas: {max_pages}")
    print(f"📄 Longitud del texto: {len(text)} caracteres")
    print(f"📄 Primeros 200 caracteres: {text[:200]}...")
    
    cover_path = None
    best_image = None
    best_size = 0
    
    # Buscar la mejor imagen de portada (la más grande)
    print(f"🔍 Buscando imágenes en las primeras {min(len(doc), 3)} páginas...")
    for i in range(min(len(doc), 3)):  # Solo revisar las primeras 3 páginas
        page_images = doc.get_page_images(i)
        print(f"📄 Página {i}: {len(page_images)} imágenes encontradas")
        
        for img in page_images:
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                print(f"🖼️ Imagen en página {i}: {pix.width}x{pix.height} (tamaño: {pix.width * pix.height})")
                
                if pix.width > 200 and pix.height > 200:  # Mínimo 200x200
                    size = pix.width * pix.height
                    if size > best_size:
                        best_size = size
                        best_image = pix
                        print(f"✅ Nueva mejor imagen: {pix.width}x{pix.height}")
            except Exception as e:
                print(f"⚠️ Error al procesar imagen en página {i}: {e}")
                continue
    
    # Guardar la mejor imagen encontrada
    if best_image:
        try:
            # Crear directorio si no existe
            os.makedirs(static_dir, exist_ok=True)
            
            # Generar nombre único para la imagen (URL-safe)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            # Limpiar el nombre para que sea URL-safe
            safe_base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_base_name = safe_base_name.replace(' ', '_')
            timestamp = int(time.time())
            cover_filename = f"cover_{safe_base_name}_{timestamp}.png"
            cover_full_path = os.path.join(static_dir, cover_filename)
            
            # Guardar imagen
            best_image.save(cover_full_path)
            cover_path = cover_filename  # Solo el nombre del archivo, no la ruta completa
            
            # Verificar que el archivo se guardó correctamente
            if os.path.exists(cover_full_path):
                file_size = os.path.getsize(cover_full_path)
                print(f"✅ Imagen de portada guardada: {cover_filename} ({file_size} bytes)")
            else:
                print(f"❌ Error: El archivo no se guardó correctamente: {cover_full_path}")
                cover_path = None
            
            print(f"✅ Imagen de portada guardada: {cover_filename}")
            print(f"✅ Tamaño de imagen: {best_image.width}x{best_image.height}")
            print(f"✅ Ruta completa: {cover_full_path}")
            
        except Exception as e:
            print(f"❌ Error al guardar imagen de portada: {e}")
            cover_path = None
        finally:
            if best_image:
                best_image = None
    else:
        print("❌ No se encontró ninguna imagen de portada válida")
        # Intentar búsqueda online como fallback
        print("🔍 Intentando búsqueda de portada online...")
        try:
            # Extraer título del nombre del archivo para la búsqueda
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            # Limpiar el nombre para la búsqueda
            search_title = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            search_title = search_title.replace('_', ' ').replace('-', ' ')
            
            online_cover = cover_search.search_book_cover_online(search_title, static_dir=static_dir)
            if online_cover:
                cover_path = online_cover
                print(f"✅ Portada online encontrada: {online_cover}")
            else:
                print("❌ No se pudo encontrar portada online")
        except Exception as e:
            print(f"❌ Error en búsqueda de portada online: {e}")
            cover_path = None
    
    return {"text": text, "cover_image_url": cover_path}

def process_epub(file_path: str, static_dir: str) -> dict:
    """ Lógica de procesamiento de EPUB muy mejorada con fallbacks para la portada. """
    book = epub.read_epub(file_path)
    text = ""
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text += soup.get_text(separator=' ') + "\n"
        if len(text) > 4500: break
    
    if len(text.strip()) < 100:
        raise HTTPException(status_code=422, detail="No se pudo extraer suficiente texto del EPUB para su análisis.")

    cover_path = None
    cover_item = None

    # Intento 1: Buscar la portada oficial en metadatos
    cover_items = list(book.get_items_of_type(ebooklib.ITEM_COVER))
    if cover_items:
        cover_item = cover_items[0]
        print(f"✅ Portada oficial encontrada en EPUB: {cover_item.get_name()}")
    
    # Intento 2: Si no hay portada oficial, buscar por nombre de archivo "cover"
    if not cover_item:
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if 'cover' in item.get_name().lower():
                cover_item = item
                print(f"✅ Portada encontrada por nombre: {item.get_name()}")
                break

    # Intento 3: Si no hay portada, buscar la primera imagen grande
    if not cover_item:
        largest_image = None
        largest_size = 0
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            try:
                content = item.get_content()
                if len(content) > 10000:  # Mínimo 10KB
                    if len(content) > largest_size:
                        largest_size = len(content)
                        largest_image = item
            except Exception as e:
                print(f"⚠️ Error al procesar imagen {item.get_name()}: {e}")
                continue
        
        if largest_image:
            cover_item = largest_image
            print(f"✅ Imagen más grande encontrada: {largest_image.get_name()} ({largest_size} bytes)")

    # Si encontramos una portada por cualquiera de los métodos
    if cover_item:
        try:
            # Crear directorio si no existe
            os.makedirs(static_dir, exist_ok=True)
            
            # Generar nombre único para la imagen (URL-safe)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            # Limpiar el nombre para que sea URL-safe
            safe_base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_base_name = safe_base_name.replace(' ', '_')
            timestamp = int(time.time())
            original_name = cover_item.get_name().replace('/', '_').replace('\\', '_')
            # Limpiar también el nombre original
            safe_original_name = "".join(c for c in original_name if c.isalnum() or c in ('.', '-', '_'))
            cover_filename = f"cover_{safe_base_name}_{timestamp}_{safe_original_name}"
            cover_full_path = os.path.join(static_dir, cover_filename)
            
            # Guardar imagen
            with open(cover_full_path, 'wb') as f:
                f.write(cover_item.get_content())
            
            cover_path = cover_filename  # Solo el nombre del archivo, no la ruta completa
            
            # Verificar que el archivo se guardó correctamente
            if os.path.exists(cover_full_path):
                file_size = os.path.getsize(cover_full_path)
                print(f"✅ Imagen de portada EPUB guardada: {cover_filename} ({file_size} bytes)")
            else:
                print(f"❌ Error: El archivo EPUB no se guardó correctamente: {cover_full_path}")
                cover_path = None
            
        except Exception as e:
            print(f"❌ Error al guardar imagen de portada EPUB: {e}")
            cover_path = None

    # Si no se encontró portada, intentar búsqueda online
    if not cover_path:
        print("🔍 Intentando búsqueda de portada online para EPUB...")
        try:
            # Extraer título del nombre del archivo para la búsqueda
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            # Limpiar el nombre para la búsqueda
            search_title = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            search_title = search_title.replace('_', ' ').replace('-', ' ')
            
            online_cover = cover_search.search_book_cover_online(search_title, static_dir=static_dir)
            if online_cover:
                cover_path = online_cover
                print(f"✅ Portada online encontrada para EPUB: {online_cover}")
            else:
                print("❌ No se pudo encontrar portada online para EPUB")
        except Exception as e:
            print(f"❌ Error en búsqueda de portada online para EPUB: {e}")
            cover_path = None

    return {"text": text, "cover_image_url": cover_path}

def translate_category_to_spanish(category: str) -> str:
    """
    Traduce categorías comunes de inglés a español
    """
    if not category or category.lower() in ["desconocido", "sin categoría", "unknown"]:
        return "Sin categoría"
    
    category_lower = category.lower().strip()
    
    # Diccionario de traducciones comunes
    translations = {
        # Psicología y Salud Mental
        "psychology": "Psicología",
        "clinical psychology": "Psicología Clínica",
        "counseling": "Consejería",
        "therapy": "Terapia",
        "mental health": "Salud Mental",
        "psychiatry": "Psiquiatría",
        
        # Literatura
        "literature": "Literatura",
        "fiction": "Ficción",
        "non-fiction": "No Ficción",
        "novel": "Novela",
        "poetry": "Poesía",
        "drama": "Drama",
        "romance": "Romance",
        "mystery": "Misterio",
        "thriller": "Suspenso",
        "fantasy": "Fantasía",
        "science fiction": "Ciencia Ficción",
        "horror": "Terror",
        "biography": "Biografía",
        "autobiography": "Autobiografía",
        
        # Ciencia y Tecnología
        "science": "Ciencia",
        "technology": "Tecnología",
        "computer science": "Informática",
        "programming": "Programación",
        "engineering": "Ingeniería",
        "mathematics": "Matemáticas",
        "physics": "Física",
        "chemistry": "Química",
        "biology": "Biología",
        "medicine": "Medicina",
        "health": "Salud",
        "medical": "Médico",
        
        # Historia y Ciencias Sociales
        "history": "Historia",
        "politics": "Política",
        "economics": "Economía",
        "sociology": "Sociología",
        "anthropology": "Antropología",
        "philosophy": "Filosofía",
        "religion": "Religión",
        "education": "Educación",
        "law": "Derecho",
        
        # Arte y Cultura
        "art": "Arte",
        "music": "Música",
        "cinema": "Cine",
        "theater": "Teatro",
        "dance": "Danza",
        "photography": "Fotografía",
        "design": "Diseño",
        "architecture": "Arquitectura",
        "fashion": "Moda",
        
        # Negocios y Administración
        "business": "Negocios",
        "management": "administración",
        "marketing": "Marketing",
        "finance": "Finanzas",
        "accounting": "Contabilidad",
        "entrepreneurship": "Emprendimiento",
        "leadership": "Liderazgo",
        
        # Otros
        "cooking": "Cocina",
        "travel": "Viajes",
        "sports": "Deportes",
        "self-help": "Autoayuda",
        "gardening": "Jardinería",
        "crafts": "Manualidades",
        "parenting": "Paternidad",
        "relationships": "Relaciones",
        "spirituality": "Espiritualidad"
    }
    
    # Buscar traducción exacta
    if category_lower in translations:
        return translations[category_lower]
    
    # Buscar traducción parcial (si contiene la palabra)
    for english, spanish in translations.items():
        if english in category_lower:
            return spanish
    
    # Si no se encuentra traducción, devolver la categoría original
    # pero capitalizada apropiadamente
    return category.strip().title()

# --- Configuración de la App FastAPI ---
app = FastAPI()
STATIC_COVERS_DIR = "static/covers"
os.makedirs(STATIC_COVERS_DIR, exist_ok=True)
STATIC_TEMP_DIR = "temp_books"
os.makedirs(STATIC_TEMP_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp_books", StaticFiles(directory=STATIC_TEMP_DIR), name="temp_books")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

# --- Rutas de la API ---
@app.post("/api/upload-book-local/", response_model=schemas.Book)
async def upload_book_local(db: Session = Depends(get_db), book_file: UploadFile = File(...)):
    """
    Sube un libro para almacenamiento local
    """
    # Crear archivo temporal para procesamiento
    temp_file_path = None
    try:
        # Crear archivo temporal
        temp_dir = "temp_processing"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"temp_{uuid.uuid4()}_{book_file.filename}")
        
        # Guardar archivo temporalmente para procesamiento
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(book_file.file, buffer)
        
        # Procesar el archivo para extraer texto Y generar portada en una sola pasada
        file_ext = os.path.splitext(book_file.filename)[1].lower()
        
        if file_ext == ".pdf":
            book_data = process_pdf(temp_file_path, STATIC_COVERS_DIR)
        elif file_ext == ".epub":
            book_data = process_epub(temp_file_path, STATIC_COVERS_DIR)
        else:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")
        
        # Usar el texto extraído para análisis con IA
        temp_text = book_data["text"]
        
        # Analizar con IA
        gemini_result = analyze_with_gemini(temp_text)
        
        # Usar resultados de IA o valores por defecto
        title = gemini_result.get("title", "Título no detectado")
        author = gemini_result.get("author", "Autor no detectado")
        category = gemini_result.get("category", "Sin categoría")
        
        # Si la IA devuelve "Desconocido", mantenerlo (no es un error)
        if title == "Título no detectado" and author == "Autor no detectado":
            title = os.path.splitext(book_file.filename)[0]
        elif title == "Desconocido":
            title = os.path.splitext(book_file.filename)[0]
        
        # La portada ya fue generada en process_pdf/process_epub, no necesitamos process_book_with_cover
        cover_image_url = book_data.get("cover_image_url")
        
        # VERIFICACIÓN DE DUPLICADOS
        duplicate_check = crud.is_duplicate_book(
            db=db,
            title=title,
            author=author,
            file_path=temp_file_path
        )
        
        if duplicate_check["is_duplicate"]:
            raise HTTPException(
                status_code=409,
                detail=f"Libro duplicado detectado: {duplicate_check['message']}"
            )
        
        # Mover archivo a ubicación permanente
        permanent_dir = "books"
        os.makedirs(permanent_dir, exist_ok=True)
        permanent_file_path = os.path.join(permanent_dir, f"{uuid.uuid4()}_{book_file.filename}")
        shutil.move(temp_file_path, permanent_file_path)
        
        # Crear registro en base de datos
        db_book = crud.create_local_book(
            db=db,
            title=title,
            author=author,
            category=category,
            cover_image_url=cover_image_url,
            file_path=permanent_file_path
        )
        
        print(f"✅ Libro subido localmente: {title}")
        return db_book
        
    except HTTPException:
        raise
    except Exception as e:
        # Limpiar archivo temporal si existe
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error al subir libro: {str(e)}")

@app.post("/upload-book/", response_model=schemas.Book)
async def upload_book(db: Session = Depends(get_db), book_file: UploadFile = File(...)):
    """
    Sube un libro directamente a Google Drive sin almacenamiento local permanente.
    """
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        if not drive_manager.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Drive no está configurado. Configure Google Drive antes de subir libros."
            )
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Google Drive no está disponible. Instale las dependencias necesarias."
        )

    # Crear archivo temporal para procesamiento
    temp_file_path = None
    try:
        # Crear archivo temporal
        temp_dir = "temp_processing"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"temp_{uuid.uuid4()}_{book_file.filename}")
        
        # Guardar archivo temporalmente para procesamiento
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(book_file.file, buffer)
        
        # Analizar con IA primero para obtener título y autor
        file_ext = os.path.splitext(book_file.filename)[1].lower()
        try:
            if file_ext == ".pdf":
                temp_book_data = process_pdf(temp_file_path, STATIC_COVERS_DIR)
            elif file_ext == ".epub":
                temp_book_data = process_epub(temp_file_path, STATIC_COVERS_DIR)
            else:
                raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")
        except HTTPException as e:
            raise e
        
        # Analizar con IA
        gemini_result = analyze_with_gemini(temp_book_data["text"])
        
        # Usar resultados de IA o valores por defecto
        title = gemini_result.get("title", "Título no detectado")
        author = gemini_result.get("author", "Autor no detectado")
        category = gemini_result.get("category", "Sin categoría")
        
        # Si la IA devuelve "Desconocido", mantenerlo (no es un error)
        # Solo usar valores por defecto si realmente hay un error
        if title == "Título no detectado" and author == "Autor no detectado":
            title = os.path.splitext(book_file.filename)[0]
        elif title == "Desconocido":
            title = os.path.splitext(book_file.filename)[0]
        
        # Procesar libro con manejo de portada
        book_data = process_book_with_cover(temp_file_path, STATIC_COVERS_DIR, title, author, should_upload_cover_to_drive=False)
        
        # VERIFICACIÓN DE DUPLICADOS ANTES DE SUBIR A GOOGLE DRIVE
        duplicate_check = crud.is_duplicate_book(
            db=db,
            title=title,
            author=author,
            file_path=temp_file_path
        )
        
        if duplicate_check["is_duplicate"]:
            raise HTTPException(
                status_code=409,  # Conflict - Duplicate
                detail=f"Libro duplicado detectado: {duplicate_check['message']}"
            )
        
        # Subir a Google Drive
        drive_result = drive_manager.upload_book_to_drive(
            file_path=temp_file_path,
            title=title,
            author=author,
            category=category
        )
        
        if not drive_result or not drive_result.get('success'):
            error_msg = drive_result.get('error', 'Error desconocido') if drive_result else 'No se pudo subir el libro a Google Drive'
            raise HTTPException(
                status_code=500, 
                detail=f"No se pudo subir el libro a Google Drive: {error_msg}"
            )
        
        print(f"✅ Libro subido a Google Drive: {title}")
        
        # Extraer la información de Drive del resultado
        drive_info = drive_result.get('drive_info', {})
        
        # Crear registro en base de datos usando la función con verificación de duplicados
        result = crud.create_book_with_duplicate_check(
            db=db, 
            title=title, 
            author=author, 
            category=category, 
            cover_image_url=book_data.get("cover_image_url"), 
            drive_info=drive_info,
            file_path=None  # No guardar ruta local
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=409,  # Conflict - Duplicate
                detail=f"Libro duplicado detectado: {result['duplicate_info']['message']}"
            )
        
        return result["book"]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass  # Ignorar errores de limpieza

@app.get("/api/books/")
def read_books(
    category: str | None = None, 
    search: str | None = None, 
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Libros por página"),
    db: Session = Depends(get_db)
):
    return crud.get_books(db, category=category, search=search, page=page, per_page=per_page)

@app.get("/api/categories/", response_model=List[str])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@app.delete("/books/bulk")
def delete_multiple_books(book_ids: dict, db: Session = Depends(get_db)):
    """
    Elimina múltiples libros por sus IDs.
    """
    if not book_ids or "book_ids" not in book_ids:
        raise HTTPException(status_code=400, detail="Se debe proporcionar al menos un ID de libro.")
    
    ids_to_delete = book_ids["book_ids"]
    if not ids_to_delete:
        raise HTTPException(status_code=400, detail="Se debe proporcionar al menos un ID de libro.")
    
    deleted_books = []
    failed_deletions = []
    
    for book_id in ids_to_delete:
        try:
            book = crud.delete_book(db, book_id=book_id)
            if book:
                deleted_books.append(book.title)
            else:
                failed_deletions.append(f"Libro con ID {book_id} no encontrado")
        except Exception as e:
            failed_deletions.append(f"Error al eliminar libro con ID {book_id}: {str(e)}")
    
    result = {
        "deleted_count": len(deleted_books),
        "deleted_books": deleted_books,
        "failed_deletions": failed_deletions
    }
    
    if not deleted_books:
        raise HTTPException(status_code=400, detail="No se pudo eliminar ningún libro.")
    
    return result

@app.delete("/api/books/{book_id}")
def delete_single_book(book_id: int, db: Session = Depends(get_db)):
    try:
        book = crud.delete_book(db, book_id=book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado.")
        return {"message": f"Libro '{book.title}' eliminado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.delete("/categories/{category_name}")
def delete_category_and_books(category_name: str, db: Session = Depends(get_db)):
    try:
        deleted_count = crud.delete_books_by_category(db, category=category_name)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Categoría '{category_name}' no encontrada o ya está vacía.")
        return {"message": f"Categoría '{category_name}' y sus {deleted_count} libros han sido eliminados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/books/download/{book_id}")
def download_local_book(book_id: int, db: Session = Depends(get_db)):
    """
    Descarga un libro local
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    
    # Verificar que el libro tenga un archivo local
    if not book.file_path or not os.path.exists(book.file_path):
        raise HTTPException(
            status_code=404, 
            detail="El archivo del libro no está disponible localmente."
        )
    
    try:
        # Determinar el tipo de archivo y nombre
        file_ext = os.path.splitext(book.file_path)[1].lower()
        
        if file_ext == '.pdf':
            return FileResponse(
                path=book.file_path,
                filename=f"{book.title}.pdf",
                media_type='application/pdf',
                content_disposition_type='inline'
            )
        elif file_ext == '.epub':
            return FileResponse(
                path=book.file_path,
                filename=f"{book.title}.epub",
                media_type='application/epub+zip',
                content_disposition_type='attachment'
            )
        else:
            return FileResponse(
                path=book.file_path,
                filename=f"{book.title}{file_ext}",
                media_type='application/octet-stream',
                content_disposition_type='attachment'
            )
            
    except Exception as e:
        print(f"❌ Error al descargar libro local: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al descargar el libro: {str(e)}"
        )

@app.get("/api/drive/books/download/{book_id}")
def download_drive_book(book_id: int, db: Session = Depends(get_db)):
    """
    Descarga un libro desde Google Drive
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    
    # Verificar que el libro esté en Google Drive
    if not book.drive_file_id:
        raise HTTPException(
            status_code=404, 
            detail="El libro no está disponible en Google Drive."
        )
    
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        if not drive_manager.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Drive no está configurado."
            )
        
        # Obtener información del archivo desde Google Drive
        file_info = drive_manager.service.files().get(
            fileId=book.drive_file_id, 
            fields='name,mimeType'
        ).execute()
        
        # Descargar archivo desde Google Drive
        temp_file_path = drive_manager.download_book_from_drive(book.drive_file_id)
        
        if not temp_file_path or not os.path.exists(temp_file_path):
            raise HTTPException(
                status_code=404, 
                detail="No se pudo descargar el archivo desde Google Drive."
            )
        
        # Usar información real del archivo desde Google Drive
        drive_filename = file_info.get('name', '')
        mime_type = file_info.get('mimeType', '')
        
        # Determinar el tipo de archivo y nombre
        if mime_type == 'application/pdf':
            filename = book.drive_filename or f"{book.title}.pdf"
            return FileResponse(
                path=temp_file_path,
                filename=filename,
                media_type='application/pdf',
                content_disposition_type='inline'
            )
        elif mime_type == 'application/epub+zip' or drive_filename.lower().endswith('.epub'):
            filename = book.drive_filename or f"{book.title}.epub"
            return FileResponse(
                path=temp_file_path,
                filename=filename,
                media_type='application/epub+zip',
                content_disposition_type='attachment'
            )
        else:
            # Fallback: usar extensión del archivo temporal
            file_ext = os.path.splitext(temp_file_path)[1].lower()
            filename = book.drive_filename or f"{book.title}{file_ext}"
            return FileResponse(
                path=temp_file_path,
                filename=filename,
                media_type=mime_type or 'application/octet-stream',
                content_disposition_type='attachment'
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al descargar libro: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al descargar el libro: {str(e)}"
        )

@app.post("/tools/convert-epub-to-pdf", response_model=schemas.ConversionResponse)
async def convert_epub_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.epub'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un EPUB.")

    epub_content = await file.read()

    try:
        import tempfile
        import zipfile
        import pathlib
        from bs4 import BeautifulSoup
        import uuid
        import fitz  # PyMuPDF para crear PDFs

        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Extraer el EPUB a una carpeta temporal
            with zipfile.ZipFile(io.BytesIO(epub_content), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # 2. Encontrar el archivo .opf (el "manifiesto" del libro)
            opf_path = next(Path(temp_dir).rglob('*.opf'), None)
            if not opf_path:
                raise Exception("No se pudo encontrar el archivo .opf en el EPUB.")
            content_root = opf_path.parent

            # 3. Leer y analizar el manifiesto .opf
            with open(opf_path, 'r', encoding='utf-8') as f:
                opf_content = f.read()
            opf_soup = BeautifulSoup(opf_content, 'xml')

            # 4. Extraer metadatos del libro
            title = "Libro EPUB"
            author = "Autor Desconocido"
            
            # Buscar título y autor en los metadatos
            dc_title = opf_soup.find('dc:title')
            if dc_title:
                title = dc_title.get_text().strip()
            
            dc_creator = opf_soup.find('dc:creator')
            if dc_creator:
                author = dc_creator.get_text().strip()

            # 5. Encontrar el orden de lectura (spine) y extraer contenido
            spine = opf_soup.find('spine')
            if not spine:
                raise Exception("No se pudo encontrar el spine en el EPUB.")

            # Mapear IDs a archivos HTML
            manifest = opf_soup.find('manifest')
            html_files = {}
            for item in manifest.find_all('item'):
                if item.get('media-type') == 'application/xhtml+xml':
                    html_files[item.get('id')] = item.get('href')

            # 6. Crear un nuevo PDF usando PyMuPDF
            pdf_doc = fitz.open()
            
            # Agregar página de título
            title_page = pdf_doc.new_page()
            title_page.insert_text(
                fitz.Point(50, 300),
                title,
                fontsize=24
            )
            title_page.insert_text(
                fitz.Point(50, 350),
                f"por {author}",
                fontsize=16
            )

            # 7. Procesar cada capítulo en el orden del spine
            spine_items = spine.find_all('itemref')
            for itemref in spine_items:
                chapter_id = itemref.get('idref')
                if chapter_id in html_files:
                    html_file = html_files[chapter_id]
                    html_path = content_root / html_file
                    
                    if html_path.exists():
                        # Leer el contenido HTML
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        # Parsear HTML y extraer texto
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Remover scripts y estilos
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extraer texto
                        text = soup.get_text()
                        
                        # Limpiar texto
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        if text.strip():
                            # Crear nueva página para el capítulo
                            page = pdf_doc.new_page()
                            
                            # Insertar texto en la página
                            text_rect = fitz.Rect(50, 50, 550, 750)
                            page.insert_textbox(
                                text_rect,
                                text,
                                fontsize=12,
                                align=fitz.TEXT_ALIGN_LEFT
                            )

            # 8. Guardar el PDF
            pdf_bytes = pdf_doc.write()
            pdf_doc.close()

        # Guardar el PDF en la carpeta temporal pública
        pdf_filename = f"{uuid.uuid4()}.pdf"
        public_pdf_path = os.path.join(STATIC_TEMP_DIR, pdf_filename)
        with open(public_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Devolver la URL de descarga en un JSON
        return {"download_url": f"/temp_books/{pdf_filename}"}
    except Exception as e:
        error_message = f"Error durante la conversión: {type(e).__name__}: {e}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

# --- Funciones de Carga Masiva ---

def is_valid_book_file(file_path: str) -> bool:
    """Verifica si un archivo es un libro válido (PDF o EPUB) o un ZIP que contenga libros"""
    valid_extensions = {'.pdf', '.epub', '.zip'}
    return Path(file_path).suffix.lower() in valid_extensions

def find_book_files(directory: str) -> List[str]:
    """Encuentra recursivamente todos los archivos de libros en un directorio, incluyendo ZIPs"""
    book_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return book_files
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and is_valid_book_file(str(file_path)):
            book_files.append(str(file_path))
    
    return book_files

def extract_books_from_zip(zip_path: str, extract_dir: str) -> List[str]:
    """Extrae libros de un archivo ZIP y retorna las rutas de los libros encontrados"""
    extracted_books = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraer todos los archivos directamente al directorio de extracción
            zip_ref.extractall(extract_dir)
            
            # Buscar archivos PDF y EPUB en el contenido extraído
            for extracted_file in Path(extract_dir).rglob('*'):
                if extracted_file.is_file() and extracted_file.suffix.lower() in {'.pdf', '.epub'}:
                    # Verificar que el archivo existe y es accesible
                    if os.path.exists(extracted_file) and os.access(extracted_file, os.R_OK):
                        extracted_books.append(str(extracted_file))
                        print(f"Archivo extraído: {extracted_file}")
                    else:
                        print(f"Archivo no accesible: {extracted_file}")
                    
    except Exception as e:
        print(f"Error al extraer ZIP {zip_path}: {e}")
    
    return extracted_books

def process_zip_containing_books(zip_path: str, temp_dir: str) -> List[str]:
    """Procesa un ZIP que puede contener libros y retorna las rutas de los libros encontrados"""
    books_found = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Verificar si el ZIP contiene archivos PDF o EPUB
            zip_contents = zip_ref.namelist()
            has_books = any(name.lower().endswith(('.pdf', '.epub')) for name in zip_contents)
            
            if has_books:
                # Extraer y procesar los libros del ZIP
                extracted_books = extract_books_from_zip(zip_path, temp_dir)
                books_found.extend(extracted_books)
                
    except Exception as e:
        print(f"Error al procesar ZIP {zip_path}: {e}")
    
    return books_found

def process_single_book_async(file_path: str, static_dir: str, db: Session) -> dict:
    """Procesa un libro individual de forma asíncrona con verificación rápida de duplicados"""
    try:
        file_extension = Path(file_path).suffix.lower()
        
        # VERIFICACIÓN RÁPIDA DE DUPLICADOS (SIN IA) - ANTES DE CUALQUIER PROCESAMIENTO
        quick_check = quick_duplicate_check(file_path, db)
        if quick_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación rápida)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": quick_check["reason"],
                    "existing_book": {
                        "id": quick_check["existing_book"].id,
                        "title": quick_check["existing_book"].title,
                        "author": quick_check["existing_book"].author,
                        "category": quick_check["existing_book"].category
                    } if quick_check["existing_book"] else None,
                    "message": quick_check["message"]
                }
            }
        
        # Verificar que el archivo existe antes de procesarlo
        if not os.path.exists(file_path):
            return {
                "success": False,
                "file": file_path,
                "error": f"Archivo no encontrado: {file_path}"
            }
        
        # Procesar el archivo según su tipo
        if file_extension == '.pdf':
            temp_result = process_pdf(file_path, static_dir)
        elif file_extension == '.epub':
            temp_result = process_epub(file_path, static_dir)
        else:
            return {"success": False, "file": file_path, "error": "Tipo de archivo no soportado"}
        
        # Analizar con IA (solo si pasó la verificación rápida)
        analysis = analyze_with_gemini(temp_result["text"])
        
        # Procesar libro con manejo de portada
        result = process_book_with_cover(file_path, static_dir, analysis["title"], analysis["author"], should_upload_cover_to_drive=False)
        
        # Verificación final de duplicados con metadatos extraídos
        duplicate_check = crud.is_duplicate_book(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            file_path=file_path
        )
        
        if duplicate_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación final)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": duplicate_check["reason"],
                    "existing_book": {
                        "id": duplicate_check["existing_book"].id,
                        "title": duplicate_check["existing_book"].title,
                        "author": duplicate_check["existing_book"].author,
                        "category": duplicate_check["existing_book"].category
                    } if duplicate_check["existing_book"] else None,
                    "message": duplicate_check["message"]
                }
            }
        
        # Subir a Google Drive (obligatorio)
        try:
            from google_drive_manager import get_drive_manager
            drive_manager = get_drive_manager()
            if not drive_manager.service:
                return {
                    "success": False,
                    "file": file_path,
                    "error": "Google Drive no está configurado"
                }
            
            drive_info = drive_manager.upload_book_to_drive(
                file_path=file_path,
                title=analysis["title"],
                author=analysis["author"],
                category=analysis["category"]
            )
            
            if not drive_info or not drive_info.get('success'):
                error_msg = drive_info.get('error', 'Error desconocido') if drive_info else 'No se pudo subir a Google Drive'
                return {
                    "success": False,
                    "file": file_path,
                    "error": f"Error al subir a Google Drive: {error_msg}"
                }
            
            print(f"✅ Libro subido a Google Drive: {analysis['title']}")
            
        except Exception as e:
            return {
                "success": False,
                "file": file_path,
                "error": f"Error al subir a Google Drive: {str(e)}"
            }
        
        # Verificar que drive_info tiene la estructura correcta
        if not drive_info or not drive_info.get('drive_info') or not drive_info['drive_info'].get('id'):
            return {
                "success": False,
                "file": file_path,
                "error": "Información de Google Drive incompleta o inválida"
            }
        
        # Guardar en base de datos
        book_result = crud.create_book_with_duplicate_check(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            category=analysis["category"],
            cover_image_url=result.get("cover_image_url"),
            drive_info=drive_info['drive_info'],  # Usar la estructura correcta
            file_path=None  # No guardar ruta local
        )
        
        if book_result["success"]:
            return {
                "success": True,
                "file": file_path,
                "book": {
                    "id": book_result["book"].id,
                    "title": book_result["book"].title,
                    "author": book_result["book"].author,
                    "category": book_result["book"].category,
                    "is_in_drive": True
                }
            }
        else:
            return {
                "success": False,
                "file": file_path,
                "error": book_result.get("duplicate_info", {}).get("message", "Error desconocido")
            }
            
    except Exception as e:
        return {
            "success": False,
            "file": file_path,
            "error": f"Error durante el procesamiento: {str(e)}"
        }

def process_single_book_local_async(file_path: str, static_dir: str, db: Session) -> dict:
    """
    Procesa un solo libro de forma asíncrona para carga masiva local
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Verificación rápida de duplicados por nombre de archivo
        quick_check = quick_duplicate_check(file_path, db)
        if quick_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación rápida)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": quick_check["reason"],
                    "existing_book": {
                        "id": quick_check["existing_book"].id,
                        "title": quick_check["existing_book"].title,
                        "author": quick_check["existing_book"].author,
                        "category": quick_check["existing_book"].category
                    } if quick_check["existing_book"] else None,
                    "message": quick_check["message"]
                }
            }
        
        # Verificar que el archivo existe antes de procesarlo
        if not os.path.exists(file_path):
            return {
                "success": False,
                "file": file_path,
                "error": f"Archivo no encontrado: {file_path}"
            }
        
        # Procesar el archivo para extraer texto Y generar portada en una sola pasada
        if file_extension == '.pdf':
            book_data = process_pdf(file_path, static_dir)
        elif file_extension == '.epub':
            book_data = process_epub(file_path, static_dir)
        else:
            return {"success": False, "file": file_path, "error": "Tipo de archivo no soportado"}
        
        # Usar el texto extraído para análisis con IA
        temp_text = book_data["text"]
        
        # Analizar con IA
        analysis = analyze_with_gemini(temp_text)
        
        # La portada ya fue generada en process_pdf/process_epub
        cover_image_url = book_data.get("cover_image_url")
        
        # Verificación final de duplicados con metadatos extraídos
        duplicate_check = crud.is_duplicate_book(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            file_path=file_path
        )
        
        if duplicate_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación final)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": duplicate_check["reason"],
                    "existing_book": {
                        "id": duplicate_check["existing_book"].id,
                        "title": duplicate_check["existing_book"].title,
                        "author": duplicate_check["existing_book"].author,
                        "category": duplicate_check["existing_book"].category
                    } if duplicate_check["existing_book"] else None,
                    "message": duplicate_check["message"]
                }
            }
        
        # Guardar en base de datos (modo local)
        book_result = crud.create_book_with_duplicate_check(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            category=analysis["category"],
            cover_image_url=cover_image_url,
            drive_info=None,  # No hay información de Drive en modo local
            file_path=file_path  # Guardar ruta local
        )
        
        if book_result["success"]:
            return {
                "success": True,
                "file": file_path,
                "book": {
                    "id": book_result["book"].id,
                    "title": book_result["book"].title,
                    "author": book_result["book"].author,
                    "category": book_result["book"].category,
                    "is_in_drive": False
                }
            }
        else:
            return {
                "success": False,
                "file": file_path,
                "error": book_result.get("duplicate_info", {}).get("message", "Error desconocido")
            }
            
    except Exception as e:
        return {
            "success": False,
            "file": file_path,
            "error": f"Error durante el procesamiento local: {str(e)}"
        }

@app.post("/upload-bulk/", response_model=schemas.BulkUploadResponse)
async def upload_bulk_books(
    folder_zip: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde un archivo ZIP que contiene una carpeta con libros (MODO NUBE)
    """
    if not folder_zip.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP.")
    
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        if not drive_manager.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Drive no está configurado. Configure Google Drive antes de subir libros."
            )
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Google Drive no está disponible. Instale las dependencias necesarias."
        )
    
    temp_extract_dir = None
    try:
        # Crear directorio temporal para extraer el ZIP
        temp_dir = "temp_bulk_upload"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generar nombre único para la carpeta de extracción temporal
        zip_name = Path(folder_zip.filename).stem
        timestamp = int(time.time())
        temp_extract_dir = os.path.join(temp_dir, f"{zip_name}_{timestamp}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        # Leer y extraer el ZIP
        zip_content = await folder_zip.read()
        
        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        # Encontrar todos los archivos de libros y ZIPs que contengan libros
        all_files = find_book_files(temp_extract_dir)
        
        # Separar archivos directos de libros y ZIPs
        direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
        zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
        
        # Procesar ZIPs que contengan libros
        books_from_zips = []
        for zip_file in zip_files:
            extracted_books = process_zip_containing_books(zip_file, temp_extract_dir)
            books_from_zips.extend(extracted_books)
        
        # Combinar todos los libros encontrados
        book_files = direct_books + books_from_zips
        
        if not book_files:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en el ZIP principal ni en los ZIPs contenidos."
            )
        
        # VERIFICACIÓN PREVIA MASIVA DE DUPLICADOS
        bulk_check_result = bulk_quick_check(book_files, db)
        unique_files = bulk_check_result["unique_files"]
        duplicate_files = bulk_check_result["duplicate_files"]
        stats = bulk_check_result["stats"]
        
        # Procesar solo archivos únicos concurrentemente
        results = []
        if unique_files:
            # Reducir workers para evitar rate limiting de la API de IA
            max_workers = min(2, len(unique_files))  # Máximo 2 workers concurrentes
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Crear tareas para cada libro único usando la función específica para carga masiva de ZIP en modo nube
                future_to_file = {
                    executor.submit(process_single_book_bulk_cloud_async, file_path, STATIC_COVERS_DIR, db): file_path
                    for file_path in unique_files
                }
                
                # Recolectar resultados con delay entre procesamientos
                for future in as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
                    
                    # Pequeño delay entre procesamientos para evitar rate limiting
                    time.sleep(0.5)
        
        # Agregar resultados de duplicados detectados en verificación previa
        for duplicate in duplicate_files:
            existing_book_dict = None
            if duplicate.get("existing_book"):
                existing_book = duplicate["existing_book"]
                existing_book_dict = {
                    "id": existing_book.id,
                    "title": existing_book.title,
                    "author": existing_book.author,
                    "category": existing_book.category
                }
            
            results.append({
                "success": False,
                "file": duplicate["file"],
                "error": "Duplicado detectado (verificación previa)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": duplicate.get("reason", "Archivo ya existe en la base de datos"),
                    "existing_book": existing_book_dict,
                    "message": duplicate.get("message", "Este archivo ya ha sido procesado anteriormente")
                }
            })
        
        # Resumen de resultados
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado (verificación previa)" and r.get("error") != "Duplicado detectado (verificación rápida)" and r.get("error") != "Duplicado detectado (verificación final)"]
        duplicates = [r for r in results if not r["success"] and (r.get("error") == "Duplicado detectado (verificación previa)" or r.get("error") == "Duplicado detectado (verificación rápida)" or r.get("error") == "Duplicado detectado (verificación final)")]
        
        return {
            "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados.",
            "total_files": len(book_files),
            "successful": len(successful),
            "failed": len(failed),
            "duplicates": len(duplicates),
            "successful_books": successful,
            "failed_files": failed,
            "duplicate_files": duplicates,
            "optimization_stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga masiva: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga masiva: {str(e)}")
    finally:
        # Limpiar directorio temporal
        if temp_extract_dir and os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
            except OSError:
                pass  # Ignorar errores de limpieza

@app.post("/api/upload-bulk-local/", response_model=schemas.BulkUploadResponse)
async def upload_bulk_books_local(
    folder_zip: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde un archivo ZIP que contiene una carpeta con libros (MODO LOCAL)
    """
    if not folder_zip.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP.")
    
    temp_extract_dir = None
    try:
        # Crear directorio temporal para extraer el ZIP
        temp_dir = "temp_bulk_upload"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generar nombre único para la carpeta de extracción temporal
        zip_name = Path(folder_zip.filename).stem
        timestamp = int(time.time())
        temp_extract_dir = os.path.join(temp_dir, f"{zip_name}_{timestamp}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        # Leer y extraer el ZIP
        zip_content = await folder_zip.read()
        
        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        # Encontrar todos los archivos de libros y ZIPs que contengan libros
        all_files = find_book_files(temp_extract_dir)
        
        # Separar archivos directos de libros y ZIPs
        direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
        zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
        
        # Procesar ZIPs que contengan libros
        books_from_zips = []
        for zip_file in zip_files:
            extracted_books = process_zip_containing_books(zip_file, temp_extract_dir)
            books_from_zips.extend(extracted_books)
        
        # Combinar todos los libros encontrados
        book_files = direct_books + books_from_zips
        
        if not book_files:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en el ZIP principal ni en los ZIPs contenidos."
            )
        
        # VERIFICACIÓN PREVIA MASIVA DE DUPLICADOS
        bulk_check_result = bulk_quick_check(book_files, db)
        unique_files = bulk_check_result["unique_files"]
        duplicate_files = bulk_check_result["duplicate_files"]
        stats = bulk_check_result["stats"]
        
        # Procesar solo archivos únicos concurrentemente
        results = []
        if unique_files:
            # Reducir workers para evitar rate limiting de la API de IA
            max_workers = min(2, len(unique_files))  # Máximo 2 workers concurrentes
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Crear tareas para cada libro único (MODO LOCAL)
                future_to_file = {
                    executor.submit(process_single_book_local_async, file_path, STATIC_COVERS_DIR, db): file_path
                    for file_path in unique_files
                }
                
                # Recolectar resultados con delay entre procesamientos
                for future in as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
                    
                    # Pequeño delay entre procesamientos para evitar rate limiting
                    time.sleep(0.5)
        
        # Agregar resultados de duplicados detectados en verificación previa
        for duplicate in duplicate_files:
            existing_book_dict = None
            if duplicate.get("existing_book"):
                existing_book = duplicate["existing_book"]
                existing_book_dict = {
                    "id": existing_book.id,
                    "title": existing_book.title,
                    "author": existing_book.author,
                    "category": existing_book.category
                }
            
            results.append({
                "success": False,
                "file": duplicate["file"],
                "error": "Duplicado detectado (verificación previa)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": duplicate.get("reason", "Archivo ya existe en la base de datos"),
                    "existing_book": existing_book_dict,
                    "message": duplicate.get("message", "Este archivo ya ha sido procesado anteriormente")
                }
            })
        
        # Resumen de resultados
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado (verificación previa)" and r.get("error") != "Duplicado detectado (verificación rápida)" and r.get("error") != "Duplicado detectado (verificación final)"]
        duplicates = [r for r in results if not r["success"] and (r.get("error") == "Duplicado detectado (verificación previa)" or r.get("error") == "Duplicado detectado (verificación rápida)" or r.get("error") == "Duplicado detectado (verificación final)")]
        
        return {
            "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados.",
            "total_files": len(book_files),
            "successful": len(successful),
            "failed": len(failed),
            "duplicates": len(duplicates),
            "successful_books": successful,
            "failed_files": failed,
            "duplicate_files": duplicates,
            "optimization_stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga masiva local: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga masiva local: {str(e)}")
    finally:
        # Limpiar directorio temporal
        if temp_extract_dir and os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
            except OSError:
                pass  # Ignorar errores de limpieza

@app.post("/upload-folder/", response_model=schemas.BulkUploadResponse)
async def upload_folder_books(
    folder_path: str = Query(..., description="Ruta de la carpeta a procesar"),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una carpeta específica del sistema (MODO NUBE)
    """
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        if not drive_manager.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Drive no está configurado. Configure Google Drive antes de subir libros."
            )
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Google Drive no está disponible. Instale las dependencias necesarias."
        )
    
    try:
        # Verificar que la carpeta existe
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(
                status_code=400, 
                detail=f"La carpeta especificada no existe o no es un directorio válido: {folder_path}"
            )
        
        # Encontrar todos los archivos de libros y ZIPs que contengan libros
        all_files = find_book_files(folder_path)
        
        # Separar archivos directos de libros y ZIPs
        direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
        zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
        
        # Procesar ZIPs que contengan libros
        books_from_zips = []
        for zip_file in zip_files:
            extracted_books = process_zip_containing_books(zip_file, folder_path)
            books_from_zips.extend(extracted_books)
        
        # Combinar todos los libros encontrados
        book_files = direct_books + books_from_zips
        
        if not book_files:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en la carpeta ni en los ZIPs contenidos."
            )
        
        # Configurar el procesamiento concurrente
        max_workers = min(2, len(book_files))  # Máximo 2 workers concurrentes
        results = []
        
        # Procesar libros en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear tareas para cada libro
            future_to_file = {
                executor.submit(process_single_book_async, file_path, STATIC_COVERS_DIR, db): file_path
                for file_path in book_files
            }
            
            # Recolectar resultados
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        # Resumen de resultados
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado (verificación rápida)" and r.get("error") != "Duplicado detectado (verificación final)"]
        duplicates = [r for r in results if not r["success"] and (r.get("error") == "Duplicado detectado (verificación rápida)" or r.get("error") == "Duplicado detectado (verificación final)")]
        
        return {
            "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados.",
            "total_files": len(book_files),
            "successful": len(successful),
            "failed": len(failed),
            "duplicates": len(duplicates),
            "successful_books": successful,
            "failed_files": failed,
            "duplicate_files": duplicates,
            "optimization_stats": {
                "total_files": len(book_files),
                "unique_files": len(successful),
                "duplicate_files": len(duplicates),
                "saved_ai_calls": len(duplicates)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga de carpeta: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga de carpeta: {str(e)}")

@app.post("/api/upload-folder-local/", response_model=schemas.BulkUploadResponse)
async def upload_folder_books_local(
    folder_path: str = Query(..., description="Ruta de la carpeta a procesar"),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una carpeta específica del sistema (MODO LOCAL)
    """
    try:
        # Verificar que la carpeta existe
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(
                status_code=400, 
                detail=f"La carpeta especificada no existe o no es un directorio válido: {folder_path}"
            )
        
        # Encontrar todos los archivos de libros y ZIPs que contengan libros
        all_files = find_book_files(folder_path)
        
        # Separar archivos directos de libros y ZIPs
        direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
        zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
        
        # Procesar ZIPs que contengan libros
        books_from_zips = []
        for zip_file in zip_files:
            extracted_books = process_zip_containing_books(zip_file, folder_path)
            books_from_zips.extend(extracted_books)
        
        # Combinar todos los libros encontrados
        book_files = direct_books + books_from_zips
        
        if not book_files:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en la carpeta ni en los ZIPs contenidos."
            )
        
        # Configurar el procesamiento concurrente
        max_workers = min(2, len(book_files))  # Máximo 2 workers concurrentes
        results = []
        
        # Procesar libros en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear tareas para cada libro (MODO LOCAL)
            future_to_file = {
                executor.submit(process_single_book_local_async, file_path, STATIC_COVERS_DIR, db): file_path
                for file_path in book_files
            }
            
            # Recolectar resultados
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        # Resumen de resultados
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado (verificación rápida)" and r.get("error") != "Duplicado detectado (verificación final)"]
        duplicates = [r for r in results if not r["success"] and (r.get("error") == "Duplicado detectado (verificación rápida)" or r.get("error") == "Duplicado detectado (verificación final)")]
        
        return {
            "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados.",
            "total_files": len(book_files),
            "successful": len(successful),
            "failed": len(failed),
            "duplicates": len(duplicates),
            "successful_books": successful,
            "failed_files": failed,
            "duplicate_files": duplicates,
            "optimization_stats": {
                "total_files": len(book_files),
                "unique_files": len(successful),
                "duplicate_files": len(duplicates),
                "saved_ai_calls": len(duplicates)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga de carpeta local: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga de carpeta local: {str(e)}")

def cleanup_orphaned_files():
    """Limpia archivos en el directorio de libros que no están referenciados en la base de datos"""
    try:
        books_dir = "books"
        if not os.path.exists(books_dir):
            return
        
        # Obtener todos los archivos en el directorio de libros
        files_in_dir = set()
        for file in os.listdir(books_dir):
            file_path = os.path.abspath(os.path.join(books_dir, file))
            if os.path.isfile(file_path):
                files_in_dir.add(file_path)
        
        # Obtener todos los archivos referenciados en la base de datos
        db = database.SessionLocal()
        try:
            books = db.query(models.Book).all()
            referenced_files = {book.file_path for book in books}
            
            # Encontrar archivos huérfanos
            orphaned_files = files_in_dir - referenced_files
            
            # Eliminar archivos huérfanos
            for orphaned_file in orphaned_files:
                try:
                    os.remove(orphaned_file)
                    print(f"Archivo huérfano eliminado: {orphaned_file}")
                except Exception as e:
                    print(f"Error al eliminar archivo huérfano {orphaned_file}: {e}")
                    
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error durante la limpieza de archivos huérfanos: {e}")

def validate_book_file(file_path: str) -> bool:
    """Valida que un archivo de libro sea accesible y válido"""
    try:
        if not os.path.exists(file_path):
            return False
        
        # Verificar que el archivo sea legible
        with open(file_path, 'rb') as f:
            f.read(1024)  # Leer los primeros 1KB para verificar acceso
        
        return True
    except Exception:
        return False

def quick_duplicate_check(file_path: str, db: Session) -> dict:
    """
    Verificación rápida de duplicados sin análisis de IA.
    Retorna información sobre si el archivo ya existe.
    """
    try:
        filename = Path(file_path).name
        file_size = os.path.getsize(file_path)
        
        # Verificar por nombre de archivo exacto
        existing_by_filename = crud.get_book_by_filename(db, filename)
        if existing_by_filename:
            return {
                "is_duplicate": True,
                "reason": "filename_exact",
                "existing_book": existing_by_filename,
                "message": f"Ya existe un libro con el mismo nombre: {filename}"
            }
        
        # Verificar por tamaño de archivo (aproximado)
        # Buscar libros con tamaño similar (±1KB de tolerancia)
        similar_size_books = db.query(models.Book).filter(
            models.Book.file_path.like(f"%{filename}%")
        ).all()
        
        for book in similar_size_books:
            if os.path.exists(book.file_path):
                existing_size = os.path.getsize(book.file_path)
                if abs(existing_size - file_size) <= 1024:  # ±1KB
                    return {
                        "is_duplicate": True,
                        "reason": "filename_size_similar",
                        "existing_book": book,
                        "message": f"Posible duplicado: {filename} (tamaño similar)"
                    }
        
        return {
            "is_duplicate": False,
            "reason": None,
            "existing_book": None,
            "message": "No se encontraron duplicados en verificación rápida"
        }
        
    except Exception as e:
        return {
            "is_duplicate": False,
            "reason": "error",
            "existing_book": None,
            "message": f"Error en verificación rápida: {str(e)}"
        }

def bulk_quick_check(book_files: List[str], db: Session) -> dict:
    """
    Verificación previa masiva de duplicados para optimizar el procesamiento.
    Retorna archivos únicos y duplicados detectados.
    """
    unique_files = []
    duplicate_files = []
    stats = {
        "total_files": len(book_files),
        "unique_files": 0,
        "duplicate_files": 0,
        "saved_ai_calls": 0
    }
    
    for file_path in book_files:
        quick_check = quick_duplicate_check(file_path, db)
        if quick_check["is_duplicate"]:
            duplicate_files.append({
                "file": file_path,
                "reason": quick_check["reason"],
                "message": quick_check["message"],
                "existing_book": quick_check["existing_book"]
            })
            stats["duplicate_files"] += 1
            stats["saved_ai_calls"] += 1
        else:
            unique_files.append(file_path)
            stats["unique_files"] += 1
    
    return {
        "unique_files": unique_files,
        "duplicate_files": duplicate_files,
        "stats": stats
    }

@app.get("/books/health-check")
def check_books_health(db: Session = Depends(get_db)):
    """
    Verifica el estado de salud de los archivos de libros en la base de datos
    """
    try:
        books = db.query(models.Book).all()
        health_report = {
            "total_books": len(books),
            "accessible_files": 0,
            "missing_files": 0,
            "orphaned_files": 0,
            "details": []
        }
        
        # Verificar archivos referenciados en la base de datos
        referenced_files = set()
        for book in books:
            file_status = validate_book_file(book.file_path)
            referenced_files.add(book.file_path)
            
            if file_status:
                health_report["accessible_files"] += 1
                health_report["details"].append({
                    "book_id": book.id,
                    "title": book.title,
                    "file_path": book.file_path,
                    "status": "accessible"
                })
            else:
                health_report["missing_files"] += 1
                health_report["details"].append({
                    "book_id": book.id,
                    "title": book.title,
                    "file_path": book.file_path,
                    "status": "missing"
                })
        
        # Verificar archivos huérfanos en el directorio de libros
        books_dir = "books"
        if os.path.exists(books_dir):
            files_in_dir = set()
            for file in os.listdir(books_dir):
                file_path = os.path.abspath(os.path.join(books_dir, file))
                if os.path.isfile(file_path):
                    files_in_dir.add(file_path)
            
            orphaned_files = files_in_dir - referenced_files
            health_report["orphaned_files"] = len(orphaned_files)
            
            for orphaned_file in orphaned_files:
                health_report["details"].append({
                    "book_id": None,
                    "title": None,
                    "file_path": orphaned_file,
                    "status": "orphaned"
                })
        
        return health_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la verificación de salud: {str(e)}")

@app.post("/books/cleanup")
def cleanup_books(db: Session = Depends(get_db)):
    """
    Ejecuta la limpieza de archivos huérfanos
    """
    try:
        cleanup_orphaned_files()
        return {"message": "Limpieza de archivos huérfanos completada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la limpieza: {str(e)}")

@app.get("/ai/status")
def check_ai_status():
    """
    Verifica el estado de la API de IA
    """
    try:
        # Hacer una llamada de prueba simple a la IA
        test_result = analyze_with_gemini("Este es un texto de prueba para verificar la API de IA.")
        
        # Mostrar información detallada sobre la respuesta
        return {
            "status": "debug",
            "message": "Respuesta detallada de la IA",
            "test_result": test_result,
            "title_check": test_result.get("title", "No encontrado"),
            "author_check": test_result.get("author", "No encontrado"),
            "category_check": test_result.get("category", "No encontrado")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar la API de IA: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/test/duplicate-detection")
def test_duplicate_detection(db: Session = Depends(get_db)):
    """
    Endpoint de prueba para verificar la detección de duplicados
    """
    try:
        # Probar con diferentes escenarios
        test_cases = [
            {
                "title": "WMO Global Annual to Decadal Climate Update 2025-2029",
                "author": "WORLD METEOROLOGICAL ORGANIZATION",
                "file_path": None,
                "description": "Libro existente - debería detectar duplicado"
            },
            {
                "title": "Libro Nuevo Test",
                "author": "Autor Nuevo",
                "file_path": None,
                "description": "Libro nuevo - no debería detectar duplicado"
            },
            {
                "title": "WMO Global Annual to Decadal Climate Update 2025-2029",
                "author": "WORLD METEOROLOGICAL ORGANIZATION",
                "file_path": "test_file.pdf",
                "description": "Libro existente con archivo - debería detectar duplicado"
            }
        ]
        
        results = []
        for test_case in test_cases:
            duplicate_check = crud.is_duplicate_book(
                db=db,
                title=test_case["title"],
                author=test_case["author"],
                file_path=test_case["file_path"]
            )
            
            results.append({
                "test_case": test_case["description"],
                "title": test_case["title"],
                "author": test_case["author"],
                "file_path": test_case["file_path"],
                "is_duplicate": duplicate_check["is_duplicate"],
                "reason": duplicate_check["reason"],
                "message": duplicate_check["message"]
            })
        
        return {
            "test_results": results,
            "message": "Pruebas de detección de duplicados completadas"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en las pruebas de duplicados: {str(e)}",
            "error_type": type(e).__name__
        }



@app.get("/api/drive/books/")
def get_drive_books(
    category: str | None = None, 
    search: str | None = None, 
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Libros por página"),
    db: Session = Depends(get_db)
):
    """
    Obtiene libros desde la base de datos que están en Google Drive con paginación
    """
    try:
        # Obtener libros de la base de datos que están en Google Drive
        books = crud.get_drive_books(db, category=category, search=search, page=page, per_page=per_page)
        
        # Los libros ya vienen como diccionarios desde crud.get_drive_books
        return books
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener libros de Drive: {str(e)}")

@app.post("/api/drive/books/upload")
async def upload_book_to_drive(book_file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Sube un libro a Google Drive
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        # Validar archivo
        if not book_file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo no válido")
        
        # Verificar si es un archivo ZIP (para procesamiento masivo)
        if book_file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="Para archivos ZIP, use el endpoint /upload-bulk/")
        
        # Crear archivo temporal
        temp_file_path = f"temp_downloads/{uuid.uuid4()}_{book_file.filename}"
        os.makedirs("temp_downloads", exist_ok=True)
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(book_file.file, buffer)
        
        try:
            # Procesar el archivo para extraer metadatos
            static_dir = "static/covers"
            os.makedirs(static_dir, exist_ok=True)
            
            if book_file.filename.lower().endswith('.pdf'):
                book_info = process_pdf(temp_file_path, static_dir)
            elif book_file.filename.lower().endswith('.epub'):
                book_info = process_epub(temp_file_path, static_dir)
            else:
                raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Solo se aceptan PDF y EPUB")
            
            # Analizar el texto con IA para extraer metadatos
            analysis = analyze_with_gemini(book_info['text'])
            
            # Procesar libro con manejo de portada
            book_data = process_book_with_cover(temp_file_path, static_dir, analysis['title'], analysis['author'], should_upload_cover_to_drive=False)
            
            # Subir a Google Drive
            drive_result = drive_manager.upload_book_to_drive(
                file_path=temp_file_path,
                title=analysis['title'],
                author=analysis['author'],
                category=analysis['category']
            )
            
            if not drive_result or not drive_result.get('success'):
                error_msg = drive_result.get('error', 'Error desconocido') if drive_result else 'No se pudo subir el libro a Google Drive'
                raise HTTPException(
                    status_code=500, 
                    detail=f"No se pudo subir el libro a Google Drive: {error_msg}"
                )
            
            print(f"✅ Libro subido a Google Drive: {analysis['title']}")
            
            # Extraer la información de Drive del resultado
            drive_info = drive_result.get('drive_info', {})
            
            # Verificar que drive_info tiene la estructura correcta
            if not drive_info or not drive_info.get('id'):
                raise HTTPException(
                    status_code=500, 
                    detail="Información de Google Drive incompleta o inválida"
                )
            
            # Crear registro en base de datos usando la función con verificación de duplicados
            result = crud.create_book_with_duplicate_check(
                db=db, 
                title=analysis['title'],
                author=analysis['author'],
                category=analysis['category'],
                cover_image_url=book_data.get("cover_image_url"), 
                drive_info=drive_info,
                file_path=None  # No guardar ruta local
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=409,  # Conflict - Duplicate
                    detail=f"Libro duplicado detectado: {result['duplicate_info']['message']}"
                )
            
            return {
                "id": result['book'].id,
                "title": analysis['title'],
                "author": analysis['author'],
                "category": analysis['category'],
                "cover_image_url": book_data.get("cover_image_url"),
                "file_path": result['book'].file_path,
                "upload_date": result['book'].upload_date.isoformat() if result['book'].upload_date else None,
                "source": "drive",
                "message": "Libro subido exitosamente a Google Drive"
            }
                
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al subir libro a Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al subir libro a Drive: {str(e)}")

@app.delete("/api/drive/books/{book_id}")
def delete_book_from_drive(book_id: str, db: Session = Depends(get_db)):
    """
    Elimina un libro de Google Drive y actualiza la base de datos local
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        import crud
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        # Buscar el libro en la base de datos local por ID
        book = crud.get_book(db, int(book_id))
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado en la base de datos")
        
        # Verificar si el libro tiene drive_file_id
        if not book.drive_file_id:
            raise HTTPException(status_code=400, detail="Este libro no está en Google Drive")
        
        # Eliminar de Google Drive primero
        result = drive_manager.delete_book_from_drive(book.drive_file_id)
        
        if result['success']:
            # Si se eliminó exitosamente de Drive, eliminar de la base de datos
            crud.delete_book(db, book.id)
            logger.info(f"Libro eliminado exitosamente de Google Drive y base de datos: {book.title}")
            return {"message": "Libro eliminado exitosamente de Google Drive y base de datos"}
        else:
            # Si el archivo no existe en Drive (error 404), eliminar de la base de datos local
            if "File not found" in result['error'] or "404" in result['error']:
                crud.delete_book(db, book.id)
                logger.info(f"Archivo no encontrado en Drive, eliminado de base de datos: {book.title}")
                return {"message": "Libro no encontrado en Google Drive, eliminado de la base de datos"}
            else:
                raise HTTPException(status_code=500, detail=f"Error al eliminar de Drive: {result['error']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar libro de Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar libro de Drive: {str(e)}")

@app.get("/api/drive/books/{book_id}/content")
def get_drive_book_content(book_id: str, db: Session = Depends(get_db)):
    """
    Obtiene el contenido de un libro desde Google Drive
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        # Buscar el libro en la base de datos por ID
        book = crud.get_book(db, int(book_id))
        
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado en la base de datos")
        
        if not book.drive_file_id:
            raise HTTPException(status_code=400, detail="Este libro no está en Google Drive")
        
        # Descargar archivo temporalmente usando el drive_file_id
        temp_file_path = drive_manager.download_book_from_drive(book.drive_file_id)
        
        if not temp_file_path or not os.path.exists(temp_file_path):
            raise HTTPException(status_code=404, detail="Libro no encontrado en Drive")
        
        try:
            # Leer contenido del archivo
            if temp_file_path.lower().endswith('.pdf'):
                # Para PDFs, devolver el archivo como respuesta de archivo con content-disposition inline
                return FileResponse(
                    path=temp_file_path,
                    media_type='application/pdf',
                    headers={
                        'Content-Disposition': 'inline',
                        'Cache-Control': 'public, max-age=3600'
                    }
                )
            elif temp_file_path.lower().endswith('.epub'):
                # Para EPUBs, extraer texto
                book_epub = epub.read_epub(temp_file_path)
                text_content = ""
                
                for item in book_epub.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        text_content += soup.get_text() + "\n"
                
                return {"content": text_content, "file_path": temp_file_path}
            else:
                raise HTTPException(status_code=400, detail="Formato de archivo no soportado para lectura")
                
        finally:
            # Limpiar archivo temporal después de un tiempo
            # En producción, implementar un sistema de limpieza más robusto
            pass
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener contenido del libro: {str(e)}")

@app.get("/api/drive/categories/")
def get_drive_categories():
    """
    Obtiene las categorías disponibles en Google Drive
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        # Obtener carpetas de categorías desde Drive
        query = f"mimeType='application/vnd.google-apps.folder' and '{drive_manager.root_folder_id}' in parents and trashed=false"
        results = drive_manager.service.files().list(q=query, spaces='drive', fields='files(name)').execute()
        
        categories = [file['name'] for file in results.get('files', [])]
        return categories
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías de Drive: {str(e)}")

@app.post("/api/drive/sync-book")
def sync_book_to_drive(book_data: dict, db: Session = Depends(get_db)):
    """
    Sincroniza un libro desde local a Google Drive y elimina el archivo local
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        book_id = book_data.get('book_id')
        title = book_data.get('title')
        author = book_data.get('author')
        category = book_data.get('category')
        
        if not all([book_id, title, author, category]):
            raise HTTPException(status_code=400, detail="Faltan datos requeridos para la sincronización")
        
        # Obtener el libro de la base de datos local
        book = crud.get_book(db, book_id=book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado en la base de datos local")
        
        # Verificar si el archivo existe
        if not book.file_path or not os.path.exists(book.file_path):
            raise HTTPException(status_code=404, detail="Archivo del libro no encontrado")
        
        # Subir a Google Drive
        result = drive_manager.upload_book_to_drive(
            book.file_path,
            title,
            author,
            category
        )
        
        if result['success']:
            # Eliminar archivo local después de subir exitosamente a Drive
            try:
                if os.path.exists(book.file_path):
                    os.remove(book.file_path)
                    print(f"Archivo local eliminado: {book.file_path}")
                
                # Eliminar imagen de portada local si existe
                if book.cover_image_url and os.path.exists(book.cover_image_url):
                    os.remove(book.cover_image_url)
                    print(f"Imagen de portada local eliminada: {book.cover_image_url}")
                    
            except OSError as e:
                print(f"Error al eliminar archivos locales: {e}")
            
            # Actualizar el libro en la base de datos para marcar que está solo en Drive
            crud.update_book_sync_status(
                db, 
                book_id=book_id, 
                synced_to_drive=True, 
                drive_file_id=result['file_id'],
                remove_local_file=True  # Marcar que el archivo local fue eliminado
            )
            
            return {
                "success": True,
                "message": "Libro sincronizado exitosamente a Google Drive y eliminado de local",
                "drive_file_id": result['file_id'],
                "drive_file_path": result['file_path'],
                "local_file_removed": True
            }
        else:
            raise HTTPException(status_code=500, detail=f"Error al subir a Drive: {result['error']}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar libro: {str(e)}")

@app.get("/api/drive/status")
def check_drive_status():
    """
    Verifica el estado de Google Drive con sistema mejorado de persistencia
    """
    try:
        # Verificar si existen los archivos de credenciales
        credentials_file = 'credentials.json'
        token_file = 'token.json'
        
        if not os.path.exists(credentials_file):
            return {
                "status": "not_configured",
                "message": "Google Drive no está configurado - faltan credenciales",
                "setup_required": True
            }
        
        # Intentar importar el drive_manager de forma segura
        try:
            from google_drive_manager import get_drive_manager
            drive_manager = get_drive_manager()
        except Exception as import_error:
            return {
                "status": "error",
                "message": f"Error al importar Google Drive Manager: {str(import_error)}",
                "setup_required": True
            }
        
        # Usar el nuevo sistema de health check con timeout
        import threading
        
        health_result = None
        error_occurred = False
        
        def health_check_with_timeout():
            nonlocal health_result, error_occurred
            try:
                health_result = drive_manager.health_check()
            except Exception as e:
                error_occurred = True
                health_result = None
        
        # Ejecutar health check con timeout de 8 segundos
        thread = threading.Thread(target=health_check_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)
        
        if thread.is_alive():
            return {
                "status": "timeout",
                "message": "Timeout al verificar Google Drive - la operación tardó demasiado",
                "setup_required": False
            }
        
        if error_occurred or health_result is None:
            return {
                "status": "error",
                "message": "No se pudo verificar la conexión con Google Drive",
                "setup_required": False
            }
        
        # Si el health check es exitoso, obtener información de almacenamiento
        if health_result['status'] == 'healthy':
            try:
                storage_info = drive_manager.get_storage_info()
                return {
                    "status": "ok",
                    "message": "Google Drive está funcionando correctamente",
                    "storage_info": storage_info,
                    "health_check": health_result,
                    "setup_required": False
                }
            except Exception as storage_error:
                return {
                    "status": "partial",
                    "message": "Conexión establecida pero error al obtener información de almacenamiento",
                    "health_check": health_result,
                    "storage_error": str(storage_error),
                    "setup_required": False
                }
        else:
            return {
                "status": "error",
                "message": health_result['message'],
                "health_check": health_result,
                "setup_required": False
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar Google Drive: {str(e)}",
            "error_type": type(e).__name__,
            "setup_required": True
        }

@app.post("/api/drive/clear-cache")
def clear_drive_cache():
    """
    Limpia el caché de Google Drive para forzar una actualización
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        # Limpiar caché
        drive_manager._clear_cache()
        
        return {
            "status": "success",
            "message": "Caché de Google Drive limpiado exitosamente",
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al limpiar caché: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/api/test/static-files")
def test_static_files():
    """
    Endpoint de prueba para verificar que los archivos estáticos se sirven correctamente
    """
    try:
        # Verificar que el directorio existe
        if not os.path.exists(STATIC_COVERS_DIR):
            return {"error": f"El directorio {STATIC_COVERS_DIR} no existe"}
        
        # Listar archivos en el directorio
        files = os.listdir(STATIC_COVERS_DIR)
        
        # Verificar que el directorio static existe
        static_dir_exists = os.path.exists("static")
        
        return {
            "static_dir_exists": static_dir_exists,
            "covers_dir_exists": os.path.exists(STATIC_COVERS_DIR),
            "covers_dir_path": os.path.abspath(STATIC_COVERS_DIR),
            "files_in_covers": files,
            "file_count": len(files)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/drive/health")
def drive_health_check():
    """
    Endpoint de health check específico para Google Drive
    """
    try:
        from google_drive_manager import get_drive_manager
        
        health_result = drive_manager.health_check()
        
        return {
            "drive_health": health_result,
            "timestamp": time.time(),
            "cache_valid": drive_manager._is_cache_valid()
        }
        
    except Exception as e:
        return {
            "drive_health": {
                "status": "error",
                "message": f"Error en health check: {str(e)}",
                "error_type": type(e).__name__
            },
            "timestamp": time.time(),
            "cache_valid": False
        }

def upload_cover_to_drive(cover_path: str, title: str, author: str) -> str:
    """
    Sube una imagen de portada a Google Drive y devuelve la URL pública
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            print("⚠️ Google Drive no está configurado, manteniendo imagen local")
            return cover_path
        
        if not cover_path or not os.path.exists(cover_path):
            print("⚠️ No hay imagen de portada para subir")
            return None
        
        # Subir imagen a Google Drive usando la función con manejo de errores robusto
        drive_info = drive_manager.upload_cover_image(
            file_path=cover_path,
            title=title,
            author=author
        )
        
        if drive_info and drive_info.get('web_view_link'):
            print(f"✅ Imagen de portada subida a Google Drive: {drive_info['web_view_link']}")
            
            # Eliminar archivo local después de subir exitosamente
            try:
                os.remove(cover_path)
                print(f"🗑️ Imagen local eliminada: {cover_path}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar imagen local: {e}")
            
            return drive_info['web_view_link']
        else:
            print("⚠️ No se pudo subir imagen a Google Drive, manteniendo local")
            return cover_path
            
    except Exception as e:
        print(f"❌ Error al subir imagen a Google Drive: {e}")
        print("⚠️ Manteniendo imagen local como fallback")
        return cover_path

def process_book_with_cover(file_path: str, static_dir: str, title: str, author: str, should_upload_cover_to_drive: bool = False) -> dict:
    """
    Procesa un libro y maneja la imagen de portada manteniendo solo las portadas locales
    
    Args:
        file_path: Ruta del archivo del libro
        static_dir: Directorio estático para guardar portadas
        title: Título del libro
        author: Autor del libro
        should_upload_cover_to_drive: Por defecto False para evitar errores SSL
    """
    print(f"🔄 Procesando libro: {os.path.basename(file_path)}")
    print(f"📁 Directorio estático: {static_dir}")
    print(f"📖 Título: {title}")
    print(f"✍️ Autor: {author}")
    print(f"☁️ Subir portada a Drive: {should_upload_cover_to_drive}")
    
    file_ext = os.path.splitext(file_path)[1].lower()
    print(f"📄 Extensión del archivo: {file_ext}")
    
    # Procesar el archivo según su tipo
    if file_ext == ".pdf":
        print("📚 Procesando PDF...")
        book_data = process_pdf(file_path, static_dir)
    elif file_ext == ".epub":
        print("📚 Procesando EPUB...")
        book_data = process_epub(file_path, static_dir)
    else:
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")
    
    # Manejar la imagen de portada
    cover_image_url = book_data.get("cover_image_url")
    print(f"🖼️ URL de portada inicial: {cover_image_url}")
    
    if cover_image_url:
        # Si la imagen se guardó localmente
        full_cover_path = os.path.join(static_dir, cover_image_url)
        print(f"📁 Ruta completa de portada: {full_cover_path}")
        print(f"📁 ¿Existe el archivo?: {os.path.exists(full_cover_path)}")
        
        if os.path.exists(full_cover_path):
            # Siempre mantener portada local para evitar errores SSL
            print("📁 Manteniendo portada local (evitando errores SSL)")
        else:
            print("❌ El archivo de portada no existe localmente")
            cover_image_url = None
    else:
        print("❌ No se encontró imagen de portada en el libro")
    
    # Si no se encontró portada local, intentar búsqueda online con información de la IA
    if not cover_image_url and title and title != "Desconocido":
        print("🔍 Intentando búsqueda de portada online con información de la IA...")
        try:
            online_cover = cover_search.search_book_cover_online(title, author, static_dir)
            if online_cover:
                cover_image_url = online_cover
                print(f"✅ Portada online encontrada con IA: {online_cover}")
            else:
                print("❌ No se pudo encontrar portada online con información de la IA")
        except Exception as e:
            print(f"❌ Error en búsqueda de portada online con IA: {e}")
    
    print(f"🖼️ URL final de portada: {cover_image_url}")
    
    return {
        "text": book_data["text"],
        "cover_image_url": cover_image_url
    }

@app.get("/api/drive/cover/{file_id}")
async def get_drive_cover(file_id: str):
    """
    Obtiene y sirve una imagen de portada desde Google Drive
    """
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            raise HTTPException(status_code=503, detail="Google Drive no está configurado")
        
        # Crear directorio para covers si no existe
        covers_dir = "static/covers"
        os.makedirs(covers_dir, exist_ok=True)
        
        # Verificar si ya tenemos la imagen descargada
        cover_filename = f"drive_cover_{file_id}.png"
        cover_path = os.path.join(covers_dir, cover_filename)
        
        if not os.path.exists(cover_path):
            # Descargar la imagen desde Google Drive
            try:
                # Intentar descargar usando la API de Google Drive
                request = drive_manager.service.files().get_media(fileId=file_id)
                with open(cover_path, 'wb') as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        logger.info(f"Descargando portada: {int(status.progress() * 100)}%")
                
                logger.info(f"Portada descargada exitosamente: {cover_filename}")
            except Exception as e:
                logger.error(f"Error al descargar portada desde Google Drive: {e}")
                # Si falla, crear una imagen placeholder
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (400, 600), color='#f0f0f0')
                draw = ImageDraw.Draw(img)
                # Intentar usar una fuente del sistema
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                draw.text((200, 300), "Sin Portada", fill='#666666', anchor="mm", font=font)
                img.save(cover_path)
                logger.info(f"Imagen placeholder creada: {cover_filename}")
        
        # Servir la imagen
        return FileResponse(
            path=cover_path,
            media_type='image/png',
            headers={'Cache-Control': 'public, max-age=3600'}
        )
        
    except Exception as e:
        logger.error(f"Error al obtener portada de Google Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener portada: {str(e)}")

@app.get("/api/test/endpoint")
def test_endpoint():
    """
    Endpoint de prueba para verificar que el servidor está funcionando
    """
    return {"message": "Endpoint de prueba funcionando correctamente"}

def process_single_book_bulk_cloud_async(file_path: str, static_dir: str, db: Session) -> dict:
    """
    Procesa un libro individual de forma asíncrona para carga masiva de ZIP en modo nube.
    Esta función es específica para el procesamiento masivo y no modifica la carga individual.
    """
    try:
        file_extension = Path(file_path).suffix.lower()
        
        # VERIFICACIÓN RÁPIDA DE DUPLICADOS (SIN IA) - ANTES DE CUALQUIER PROCESAMIENTO
        quick_check = quick_duplicate_check(file_path, db)
        if quick_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación rápida)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": quick_check["reason"],
                    "existing_book": {
                        "id": quick_check["existing_book"].id,
                        "title": quick_check["existing_book"].title,
                        "author": quick_check["existing_book"].author,
                        "category": quick_check["existing_book"].category
                    } if quick_check["existing_book"] else None,
                    "message": quick_check["message"]
                }
            }
        
        # Verificar que el archivo existe antes de procesarlo
        if not os.path.exists(file_path):
            return {
                "success": False,
                "file": file_path,
                "error": f"Archivo no encontrado: {file_path}"
            }
        
        # Procesar el archivo según su tipo
        if file_extension == '.pdf':
            temp_result = process_pdf(file_path, static_dir)
        elif file_extension == '.epub':
            temp_result = process_epub(file_path, static_dir)
        else:
            return {"success": False, "file": file_path, "error": "Tipo de archivo no soportado"}
        
        # Analizar con IA (solo si pasó la verificación rápida)
        analysis = analyze_with_gemini(temp_result["text"])
        
        # Procesar libro con manejo de portada
        result = process_book_with_cover(file_path, static_dir, analysis["title"], analysis["author"], should_upload_cover_to_drive=False)
        
        # Verificación final de duplicados con metadatos extraídos
        duplicate_check = crud.is_duplicate_book(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            file_path=file_path
        )
        
        if duplicate_check["is_duplicate"]:
            return {
                "success": False,
                "file": file_path,
                "error": "Duplicado detectado (verificación final)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": duplicate_check["reason"],
                    "existing_book": {
                        "id": duplicate_check["existing_book"].id,
                        "title": duplicate_check["existing_book"].title,
                        "author": duplicate_check["existing_book"].author,
                        "category": duplicate_check["existing_book"].category
                    } if duplicate_check["existing_book"] else None,
                    "message": duplicate_check["message"]
                }
            }
        
        # Subir a Google Drive (obligatorio para modo nube)
        try:
            from google_drive_manager import get_drive_manager
            drive_manager = get_drive_manager()
            if not drive_manager.service:
                return {
                    "success": False,
                    "file": file_path,
                    "error": "Google Drive no está configurado"
                }
            
            drive_result = drive_manager.upload_book_to_drive(
                file_path=file_path,
                title=analysis["title"],
                author=analysis["author"],
                category=analysis["category"]
            )
            
            if not drive_result or not drive_result.get('success'):
                error_msg = drive_result.get('error', 'Error desconocido') if drive_result else 'No se pudo subir a Google Drive'
                return {
                    "success": False,
                    "file": file_path,
                    "error": f"Error al subir a Google Drive: {error_msg}"
                }
            
            print(f"✅ Libro subido a Google Drive: {analysis['title']}")
            
        except Exception as e:
            return {
                "success": False,
                "file": file_path,
                "error": f"Error al subir a Google Drive: {str(e)}"
            }
        
        # Verificar que drive_result tiene la estructura correcta para carga masiva
        if not drive_result or not drive_result.get('drive_info') or not drive_result['drive_info'].get('id'):
            return {
                "success": False,
                "file": file_path,
                "error": "Información de Google Drive incompleta o inválida"
            }
        
        # Guardar en base de datos usando la estructura específica para carga masiva
        book_result = crud.create_book_with_duplicate_check(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            category=analysis["category"],
            cover_image_url=result.get("cover_image_url"),
            drive_info=drive_result['drive_info'],  # Estructura específica para carga masiva
            file_path=None  # No guardar ruta local en modo nube
        )
        
        if book_result["success"]:
            return {
                "success": True,
                "file": file_path,
                "book": {
                    "id": book_result["book"].id,
                    "title": book_result["book"].title,
                    "author": book_result["book"].author,
                    "category": book_result["book"].category,
                    "is_in_drive": True
                }
            }
        else:
            return {
                "success": False,
                "file": file_path,
                "error": book_result.get("duplicate_info", {}).get("message", "Error desconocido")
            }
            
    except Exception as e:
        return {
            "success": False,
            "file": file_path,
            "error": f"Error durante el procesamiento masivo: {str(e)}"
        }

@app.post("/api/books/{book_id}/search-cover-online")
async def search_cover_online(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    Busca una portada online para un libro existente
    """
    try:
        # Obtener el libro de la base de datos
        book = crud.get_book(db, book_id=book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        print(f"🔍 Buscando portada online para: '{book.title}' por '{book.author}'")
        
        # Buscar portada online
        online_cover = cover_search.search_book_cover_online(book.title, book.author, "static/covers")
        
        if online_cover:
            # Actualizar el libro con la nueva portada
            book_update = {"cover_image_url": online_cover}
            updated_book = crud.update_book(db, book_id=book_id, book_update=book_update)
            
            return {
                "success": True,
                "message": f"Portada online encontrada y actualizada: {online_cover}",
                "cover_url": online_cover,
                "book": {
                    "id": updated_book.id,
                    "title": updated_book.title,
                    "author": updated_book.author,
                    "cover_image_url": updated_book.cover_image_url
                }
            }
        else:
            return {
                "success": False,
                "message": "No se pudo encontrar una portada online para este libro"
            }
            
    except Exception as e:
        logger.error(f"Error al buscar portada online: {e}")
        raise HTTPException(status_code=500, detail=f"Error al buscar portada online: {str(e)}")

@app.post("/api/books/{book_id}/update-cover")
async def update_book_cover(
    book_id: int, 
    cover_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Actualiza la portada de un libro
    """
    try:
        # Verificar que el libro existe
        book = crud.get_book(db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que el archivo es una imagen
        if not cover_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        # Leer el contenido del archivo para generar hash
        content = await cover_file.read()
        import hashlib
        file_hash = hashlib.md5(content).hexdigest()
        
        # Verificar si ya existe una portada con el mismo hash
        existing_cover = None
        covers_dir = os.path.join("static", "covers")
        for filename in os.listdir(covers_dir):
            if filename.startswith(f"cover_{book_id}_"):
                file_path = os.path.join(covers_dir, filename)
                try:
                    with open(file_path, 'rb') as f:
                        existing_content = f.read()
                        existing_hash = hashlib.md5(existing_content).hexdigest()
                        if existing_hash == file_hash:
                            existing_cover = filename
                            break
                except:
                    continue
        
        # Si ya existe una portada idéntica, no hacer nada
        if existing_cover:
            return {
                "message": "La portada ya existe y es idéntica", 
                "cover_url": f"/static/covers/{existing_cover}"
            }
        
        # Generar nombre único para la portada
        file_extension = os.path.splitext(cover_file.filename)[1]
        cover_filename = f"cover_{book_id}_{int(time.time())}{file_extension}"
        cover_path = os.path.join("static", "covers", cover_filename)
        
        # Guardar la nueva portada
        with open(cover_path, "wb") as buffer:
            buffer.write(content)
        
        # Eliminar la portada anterior si existe
        if book.cover_image_url:
            old_cover_path = book.cover_image_url.replace("http://localhost:8001/static/covers/", "")
            old_cover_full_path = os.path.join("static", "covers", old_cover_path)
            if os.path.exists(old_cover_full_path):
                os.remove(old_cover_full_path)
        
        # Actualizar la base de datos
        book.cover_image_url = f"/static/covers/{cover_filename}"
        db.commit()
        
        return {"message": "Portada actualizada exitosamente", "cover_url": book.cover_image_url}
        
    except Exception as e:
        logger.error(f"Error actualizando portada: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la portada")

@app.put("/api/books/{book_id}")
async def update_book(
    book_id: int,
    book_update: dict,
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un libro (título, autor, categoría)
    """
    try:
        book = crud.get_book(db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Actualizar campos permitidos
        if 'title' in book_update:
            book.title = book_update['title']
        if 'author' in book_update:
            book.author = book_update['author']
        if 'category' in book_update:
            book.category = book_update['category']
        
        db.commit()
        db.refresh(book)
        
        return book
        
    except Exception as e:
        logger.error(f"Error actualizando libro: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el libro")

@app.post("/api/categories/")
async def create_category(
    category_data: dict,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva categoría y la sincroniza con la nube
    """
    try:
        category_name = category_data.get('name')
        if not category_name:
            raise HTTPException(status_code=400, detail="El nombre de la categoría es requerido")
        
        # Verificar si la categoría ya existe
        existing_books = crud.get_books_by_category(db, category_name)
        if existing_books:
            return {"message": "La categoría ya existe", "category": category_name}
        
        # Crear la categoría (se crea automáticamente al agregar un libro)
        # Aquí solo verificamos que se pueda crear
        return {"message": "Categoría creada exitosamente", "category": category_name}
        
    except Exception as e:
        logger.error(f"Error creando categoría: {e}")
        raise HTTPException(status_code=500, detail="Error al crear la categoría")

@app.get("/api/books/{book_id}/open")
async def open_local_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    Abre un libro local para lectura
    """
    try:
        book = crud.get_book(db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar que el libro tiene archivo local
        if not book.file_path or not os.path.exists(book.file_path):
            raise HTTPException(status_code=404, detail="Archivo del libro no encontrado")
        
        # Servir el archivo
        return FileResponse(
            book.file_path,
            media_type='application/octet-stream',
            filename=os.path.basename(book.file_path)
        )
        
    except Exception as e:
        logger.error(f"Error abriendo libro: {e}")
        raise HTTPException(status_code=500, detail="Error al abrir el libro")

@app.delete("/api/covers/{cover_filename}")
async def delete_cover(
    cover_filename: str,
    db: Session = Depends(get_db)
):
    """
    Elimina una portada específica
    """
    try:
        cover_path = os.path.join("static", "covers", cover_filename)
        if os.path.exists(cover_path):
            os.remove(cover_path)
            return {"message": "Portada eliminada exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Portada no encontrada")
            
    except Exception as e:
        logger.error(f"Error eliminando portada: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar la portada")

@app.post("/api/books/bulk-search-covers")
async def bulk_search_covers(
    book_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Busca portadas online para múltiples libros en lote
    """
    try:
        results = []
        successful = 0
        failed = 0
        
        for book_id in book_ids:
            try:
                # Obtener el libro
                book = crud.get_book(db, book_id=book_id)
                if not book:
                    results.append({
                        "book_id": book_id,
                        "success": False,
                        "message": "Libro no encontrado"
                    })
                    failed += 1
                    continue
                
                # Buscar portada online
                online_cover = cover_search.search_book_cover_online(book.title, book.author, "static/covers")
                
                if online_cover:
                    # Actualizar el libro
                    book_update = {"cover_image_url": online_cover}
                    updated_book = crud.update_book(db, book_id=book_id, book_update=book_update)
                    
                    results.append({
                        "book_id": book_id,
                        "success": True,
                        "message": f"Portada encontrada: {online_cover}",
                        "cover_url": online_cover,
                        "title": book.title
                    })
                    successful += 1
                else:
                    results.append({
                        "book_id": book_id,
                        "success": False,
                        "message": "No se encontró portada online",
                        "title": book.title
                    })
                    failed += 1
                    
            except Exception as e:
                results.append({
                    "book_id": book_id,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
                failed += 1
        
        return {
            "success": True,
            "message": f"Búsqueda completada: {successful} exitosas, {failed} fallidas",
            "total_books": len(book_ids),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda masiva de portadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda masiva: {str(e)}")

@app.post("/api/covers/cleanup")
async def cleanup_orphaned_covers(db: Session = Depends(get_db)):
    """
    Limpia portadas huérfanas que no están asociadas a ningún libro
    Solo elimina archivos que no están siendo utilizados por libros activos
    """
    try:
        covers_dir = os.path.join("static", "covers")
        if not os.path.exists(covers_dir):
            return {"message": "No existe el directorio de portadas", "deleted_count": 0}
        
        # Obtener todas las portadas en uso
        books = db.query(models.Book).all()
        used_covers = set()
        
        for book in books:
            if book.cover_image_url:
                # Extraer el nombre del archivo de la URL de diferentes formatos
                cover_filename = None
                
                if book.cover_image_url.startswith('/static/covers/'):
                    cover_filename = book.cover_image_url.replace('/static/covers/', '')
                elif book.cover_image_url.startswith('http://localhost:8001/static/covers/'):
                    cover_filename = book.cover_image_url.replace('http://localhost:8001/static/covers/', '')
                elif '/' not in book.cover_image_url and '.' in book.cover_image_url:
                    # Es solo el nombre del archivo
                    cover_filename = book.cover_image_url
                elif 'drive.google.com' in book.cover_image_url:
                    # Es una URL de Google Drive, extraer el ID del archivo
                    if '/file/d/' in book.cover_image_url:
                        file_id = book.cover_image_url.split('/file/d/')[1].split('/')[0]
                        cover_filename = f"drive_cover_{file_id}.png"
                
                if cover_filename:
                    used_covers.add(cover_filename)
                    logger.info(f"Portada en uso: {cover_filename} (libro ID: {book.id})")
        
        # Buscar portadas huérfanas
        orphaned_covers = []
        total_files = 0
        
        for filename in os.listdir(covers_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                total_files += 1
                if filename not in used_covers:
                    orphaned_covers.append(filename)
                    logger.info(f"Portada huérfana detectada: {filename}")
        
        # Eliminar portadas huérfanas
        deleted_count = 0
        deleted_files = []
        
        for filename in orphaned_covers:
            try:
                file_path = os.path.join(covers_dir, filename)
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                deleted_files.append({
                    "filename": filename,
                    "size_mb": round(file_size / (1024 * 1024), 2)
                })
                logger.info(f"✅ Portada huérfana eliminada: {filename} ({round(file_size / (1024 * 1024), 2)} MB)")
            except Exception as e:
                logger.error(f"❌ Error eliminando portada {filename}: {e}")
        
        # Calcular espacio liberado
        total_size_freed = sum(file["size_mb"] for file in deleted_files)
        
        return {
            "message": f"Limpieza completada. {deleted_count} portadas huérfanas eliminadas de {total_files} archivos totales. {total_size_freed} MB liberados.",
            "deleted_count": deleted_count,
            "total_files": total_files,
            "used_covers": len(used_covers),
            "size_freed_mb": total_size_freed,
            "deleted_files": deleted_files,
            "orphaned_covers": orphaned_covers
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de portadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al limpiar portadas: {str(e)}")

@app.post("/api/cleanup-temp-files")
async def cleanup_temp_files():
    """
    Limpia todos los archivos temporales generados por la aplicación
    """
    try:
        temp_directories = [
            "temp_processing",
            "temp_bulk_upload", 
            "temp_downloads",
            "temp_books"
        ]
        
        total_deleted = 0
        total_size_freed = 0
        cleanup_results = {}
        
        for temp_dir in temp_directories:
            if os.path.exists(temp_dir):
                try:
                    # Contar archivos y calcular tamaño antes de eliminar
                    file_count = 0
                    dir_size = 0
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                dir_size += os.path.getsize(file_path)
                                file_count += 1
                            except OSError:
                                pass
                    
                    # Eliminar directorio completo
                    shutil.rmtree(temp_dir)
                    
                    # Recrear directorio vacío
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    cleanup_results[temp_dir] = {
                        "files_deleted": file_count,
                        "size_freed_mb": round(dir_size / (1024 * 1024), 2),
                        "status": "success"
                    }
                    
                    total_deleted += file_count
                    total_size_freed += dir_size
                    
                    logger.info(f"🗑️ Directorio temporal limpiado: {temp_dir} ({file_count} archivos, {round(dir_size / (1024 * 1024), 2)} MB)")
                    
                except Exception as e:
                    cleanup_results[temp_dir] = {
                        "files_deleted": 0,
                        "size_freed_mb": 0,
                        "status": "error",
                        "error": str(e)
                    }
                    logger.error(f"⚠️ Error al limpiar directorio {temp_dir}: {e}")
            else:
                cleanup_results[temp_dir] = {
                    "files_deleted": 0,
                    "size_freed_mb": 0,
                    "status": "not_found"
                }
        
        return {
            "message": f"Limpieza de archivos temporales completada. {total_deleted} archivos eliminados, {round(total_size_freed / (1024 * 1024), 2)} MB liberados.",
            "total_files_deleted": total_deleted,
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            "directories_cleaned": cleanup_results
        }
        
    except Exception as e:
        logger.error(f"Error durante la limpieza de archivos temporales: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la limpieza de archivos temporales: {str(e)}")

@app.post("/api/upload-folder-local/", response_model=schemas.BulkUploadResponse)
async def upload_folder_books_local(
    folder_path: str = Query(..., description="Ruta de la carpeta a procesar"),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una carpeta específica del sistema (MODO LOCAL)
    """
    try:
        # Verificar que la carpeta existe
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(
                status_code=400, 
                detail=f"La carpeta especificada no existe o no es un directorio válido: {folder_path}"
            )
        
        # Encontrar todos los archivos de libros y ZIPs que contengan libros
        all_files = find_book_files(folder_path)
        
        # Separar archivos directos de libros y ZIPs
        direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
        zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
        
        # Procesar ZIPs que contengan libros
        books_from_zips = []
        for zip_file in zip_files:
            extracted_books = process_zip_containing_books(zip_file, folder_path)
            books_from_zips.extend(extracted_books)
        
        # Combinar todos los libros encontrados
        book_files = direct_books + books_from_zips
        
        if not book_files:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en la carpeta ni en los ZIPs contenidos."
            )
        
        # Configurar el procesamiento concurrente
        max_workers = min(2, len(book_files))  # Máximo 2 workers concurrentes
        results = []
        
        # Procesar libros en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear tareas para cada libro (MODO LOCAL)
            future_to_file = {
                executor.submit(process_single_book_local_async, file_path, STATIC_COVERS_DIR, db): file_path
                for file_path in book_files
            }
            
            # Recolectar resultados
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        # Resumen de resultados
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado (verificación rápida)" and r.get("error") != "Duplicado detectado (verificación final)"]
        duplicates = [r for r in results if not r["success"] and (r.get("error") == "Duplicado detectado (verificación rápida)" or r.get("error") == "Duplicado detectado (verificación final)")]
        
        return {
            "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados.",
            "total_files": len(book_files),
            "successful": len(successful),
            "failed": len(failed),
            "duplicates": len(duplicates),
            "successful_books": successful,
            "failed_files": failed,
            "duplicate_files": duplicates,
            "optimization_stats": {
                "total_files": len(book_files),
                "unique_files": len(successful),
                "duplicate_files": len(duplicates),
                "saved_ai_calls": len(duplicates)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga de carpeta local: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga de carpeta local: {str(e)}")

@app.post("/api/upload-drive-folder/", response_model=schemas.BulkUploadResponse)
async def upload_drive_folder_books(
    folder_data: dict,
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una carpeta pública de Google Drive (MODO NUBE)
    """
    folder_url = folder_data.get('folder_url')
    if not folder_url:
        raise HTTPException(status_code=400, detail="Se requiere la URL de la carpeta de Google Drive")
    
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        if not drive_manager.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Drive no está configurado. Configure Google Drive antes de subir libros."
            )
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Google Drive no está disponible. Instale las dependencias necesarias."
        )
    
    temp_dir = None
    try:
        # Crear directorio temporal para descargar archivos
        temp_dir = "temp_drive_upload"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Procesar la carpeta pública recursivamente
        print(f"🔍 Procesando carpeta pública: {folder_url}")
        
        # Verificar accesibilidad de la carpeta primero
        print(f"🔍 Verificando accesibilidad de la carpeta...")
        accessibility_check = drive_manager.check_folder_accessibility(folder_url)
        
        if not accessibility_check["success"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Error de accesibilidad: {accessibility_check['error']}"
            )
        
        print(f"✅ Carpeta accesible - Propietario: {accessibility_check.get('owner', 'Desconocido')}")
        
        folder_result = drive_manager.process_public_folder_recursively(folder_url, temp_dir)
        
        if not folder_result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Error al procesar la carpeta: {folder_result['error']}"
            )
        
        books_info = folder_result["books"]
        folder_info = folder_result["folder_info"]
        
        if not books_info:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron archivos PDF o EPUB válidos en la carpeta pública."
            )
        
        print(f"📚 Libros encontrados: {len(books_info)}")
        
        # Descargar y procesar cada libro
        results = []
        successful = 0
        failed = 0
        duplicates = 0
        
        for i, book_info in enumerate(books_info):
            try:
                print(f"📖 Procesando libro {i + 1}/{len(books_info)}: {book_info['name']}")
                
                # Descargar archivo desde Google Drive
                download_result = drive_manager.download_file_from_drive(book_info['id'], temp_dir)
                
                if not download_result["success"]:
                    print(f"❌ Error al descargar {book_info['name']}: {download_result['error']}")
                    results.append({
                        "success": False,
                        "file": book_info['name'],
                        "error": f"Error al descargar: {download_result['error']}"
                    })
                    failed += 1
                    continue
                
                file_path = download_result["file_path"]
                
                # Procesar el libro (modo nube)
                result = process_single_book_bulk_cloud_async(file_path, STATIC_COVERS_DIR, db)
                
                if result["success"]:
                    successful += 1
                    print(f"✅ {book_info['name']} procesado exitosamente")
                else:
                    if "Duplicado detectado" in result.get("error", ""):
                        duplicates += 1
                        print(f"⚠️ {book_info['name']} es un duplicado")
                    else:
                        failed += 1
                        print(f"❌ Error procesando {book_info['name']}: {result.get('error')}")
                
                results.append(result)
                
                # Limpiar archivo temporal
                try:
                    os.remove(file_path)
                except:
                    pass
                
            except Exception as e:
                print(f"❌ Error procesando {book_info['name']}: {e}")
                results.append({
                    "success": False,
                    "file": book_info['name'],
                    "error": f"Error de procesamiento: {str(e)}"
                })
                failed += 1
        
        # Resumen final
        print(f"🎉 Procesamiento completado: {successful} exitosos, {failed} fallidos, {duplicates} duplicados")
        
        return {
            "message": f"Procesamiento completado. {successful} libros procesados exitosamente, {failed} fallaron, {duplicates} duplicados detectados.",
            "total_files": len(books_info),
            "successful": successful,
            "failed": failed,
            "duplicates": duplicates,
            "successful_books": [r for r in results if r["success"]],
            "failed_files": [r for r in results if not r["success"] and "Duplicado detectado" not in r.get("error", "")],
            "duplicate_files": [r for r in results if not r["success"] and "Duplicado detectado" in r.get("error", "")],
            "optimization_stats": {
                "total_files": len(books_info),
                "unique_files": successful,
                "duplicate_files": duplicates,
                "saved_ai_calls": duplicates  # Cada duplicado evita una llamada a la IA
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga de carpeta de Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga de carpeta de Drive: {str(e)}")
    finally:
        # Limpiar directorio temporal
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass  # Ignorar errores de limpieza

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
