from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Response
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

import crud, models, database, schemas

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
    1. Para el TÍTULO: Busca el título principal del libro, generalmente en mayúsculas o al inicio del texto
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
    for i in range(min(len(doc), 5)): text += doc.load_page(i).get_text("text", sort=True)
    cover_path = None
    for i in range(len(doc)):
        for img in doc.get_page_images(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.width > 300 and pix.height > 300:
                cover_filename = f"cover_{os.path.basename(file_path)}.png"
                cover_full_path = os.path.join(static_dir, cover_filename)
                pix.save(cover_full_path)
                cover_path = f"{static_dir}/{cover_filename}"
                break
        if cover_path: break
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
    
    # Intento 2: Si no hay portada oficial, buscar por nombre de archivo "cover"
    if not cover_item:
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if 'cover' in item.get_name().lower():
                cover_item = item
                break

    # Si encontramos una portada por cualquiera de los métodos
    if cover_item:
        cover_filename = f"cover_{os.path.basename(file_path)}_{cover_item.get_name()}".replace('/', '_').replace('\\', '_')
        cover_full_path = os.path.join(static_dir, cover_filename)
        with open(cover_full_path, 'wb') as f: f.write(cover_item.get_content())
        cover_path = f"{static_dir}/{cover_filename}"

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
        "management": "Administración",
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
@app.post("/upload-book/", response_model=schemas.Book)
async def upload_book(db: Session = Depends(get_db), book_file: UploadFile = File(...)):
    """
    Sube un libro directamente a Google Drive sin almacenamiento local permanente.
    """
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import drive_manager
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
        
        # Procesar el archivo según su tipo
        file_ext = os.path.splitext(book_file.filename)[1].lower()
        try:
            if file_ext == ".pdf":
                book_data = process_pdf(temp_file_path, STATIC_COVERS_DIR)
            elif file_ext == ".epub":
                book_data = process_epub(temp_file_path, STATIC_COVERS_DIR)
            else:
                raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")
        except HTTPException as e:
            raise e
        
        # Analizar con IA
        gemini_result = analyze_with_gemini(book_data["text"])
        
        # Usar resultados de IA o valores por defecto
        title = gemini_result.get("title", "Título no detectado")
        author = gemini_result.get("author", "Autor no detectado")
        category = gemini_result.get("category", "Sin categoría")
        
        # Si la IA devuelve "Desconocido", mantenerlo (no es un error)
        # Solo usar valores por defecto si realmente hay un error
        if title == "Título no detectado" and author == "Autor no detectado":
            # Si la IA no pudo detectar nada, usar el nombre del archivo como título
            title = os.path.splitext(book_file.filename)[0]
        elif title == "Desconocido":
            # Si la IA devuelve "Desconocido" para el título, usar el nombre del archivo
            title = os.path.splitext(book_file.filename)[0]
        
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
        drive_info = drive_manager.upload_book_to_drive(
            file_path=temp_file_path,
            title=title,
            author=author,
            category=category
        )
        
        if not drive_info:
            raise HTTPException(
                status_code=500, 
                detail="No se pudo subir el libro a Google Drive. Intente nuevamente."
            )
        
        print(f"✅ Libro subido a Google Drive: {title}")
        
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

@app.get("/books/", response_model=List[schemas.Book])
def read_books(category: str | None = None, search: str | None = None, db: Session = Depends(get_db)):
    return crud.get_books(db, category=category, search=search)

@app.get("/categories/", response_model=List[str])
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

@app.delete("/books/{book_id}")
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

@app.get("/books/download/{book_id}")
def download_book(book_id: int, db: Session = Depends(get_db)):
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
        from google_drive_manager import drive_manager
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
        from weasyprint import HTML, CSS
        from bs4 import BeautifulSoup
        import uuid

        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Extraer el EPUB a una carpeta temporal
            with zipfile.ZipFile(io.BytesIO(epub_content), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # 2. Encontrar el archivo .opf (el "manifiesto" del libro)
            opf_path = next(Path(temp_dir).rglob('*.opf'), None)
            if not opf_path:
                raise Exception("No se pudo encontrar el archivo .opf en el EPUB.")
            content_root = opf_path.parent

            # 3. Leer y analizar el manifiesto .opf en modo binario para autodetectar codificación
            with open(opf_path, 'rb') as f:
                opf_soup = BeautifulSoup(f, 'lxml-xml')

            # 4. Crear una página de portada si se encuentra
            html_docs = []
            cover_meta = opf_soup.find('meta', {'name': 'cover'})
            if cover_meta:
                cover_id = cover_meta.get('content')
                cover_item = opf_soup.find('item', {'id': cover_id})
                if cover_item:
                    cover_href = cover_item.get('href')
                    cover_path = content_root / cover_href
                    if cover_path.exists():
                        cover_html_string = f"<html><body style='text-align: center; margin: 0; padding: 0;'><img src='{cover_path.as_uri()}' style='width: 100%; height: 100%; object-fit: contain;'/></body></html>"
                        html_docs.append(HTML(string=cover_html_string))

            # 5. Encontrar y leer todos los archivos CSS
            stylesheets = []
            css_items = opf_soup.find_all('item', {'media-type': 'text/css'})
            for css_item in css_items:
                css_href = css_item.get('href')
                if css_href:
                    css_path = content_root / css_href
                    if css_path.exists():
                        stylesheets.append(CSS(filename=css_path))

            # 6. Encontrar el orden de lectura (spine) y añadir los capítulos
            spine_ids = [item.get('idref') for item in opf_soup.find('spine').find_all('itemref')]
            html_paths_map = {item['id']: item['href'] for item in opf_soup.find_all('item', {'media-type': 'application/xhtml+xml'})}
            
            for chapter_id in spine_ids:
                href = html_paths_map.get(chapter_id)
                if href:
                    chapter_path = content_root / href
                    if chapter_path.exists():
                        # LA SOLUCIÓN: Pasar filename y encoding directamente a WeasyPrint
                        html_docs.append(HTML(filename=chapter_path, encoding='utf-8'))

            if not html_docs:
                raise Exception("No se encontró contenido HTML en el EPUB.")

            # 7. Renderizar y unir todos los documentos
            first_doc = html_docs[0].render(stylesheets= stylesheets)
            all_pages = [p for doc in html_docs[1:] for p in doc.render(stylesheets= stylesheets).pages]
            
            pdf_bytes_io = io.BytesIO()
            first_doc.copy(all_pages).write_pdf(target=pdf_bytes_io)
            pdf_bytes = pdf_bytes_io.getvalue()

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
            result = process_pdf(file_path, static_dir)
        elif file_extension == '.epub':
            result = process_epub(file_path, static_dir)
        else:
            return {"success": False, "file": file_path, "error": "Tipo de archivo no soportado"}
        
        # Analizar con IA (solo si pasó la verificación rápida)
        analysis = analyze_with_gemini(result["text"])
        
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
            from google_drive_manager import drive_manager
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
            
            if not drive_info:
                return {
                    "success": False,
                    "file": file_path,
                    "error": "No se pudo subir a Google Drive"
                }
            
            print(f"✅ Libro subido a Google Drive: {analysis['title']}")
            
        except Exception as e:
            return {
                "success": False,
                "file": file_path,
                "error": f"Error al subir a Google Drive: {str(e)}"
            }
        
        # Guardar en base de datos
        book_result = crud.create_book_with_duplicate_check(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            category=analysis["category"],
            cover_image_url=result.get("cover_image_url"),
            drive_info=drive_info,
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

@app.post("/upload-bulk/", response_model=schemas.BulkUploadResponse)
async def upload_bulk_books(
    folder_zip: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde un archivo ZIP que contiene una carpeta con libros
    """
    if not folder_zip.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP.")
    
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import drive_manager
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
                # Crear tareas para cada libro único
                future_to_file = {
                    executor.submit(process_single_book_async, file_path, STATIC_COVERS_DIR, db): file_path
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
            results.append({
                "success": False,
                "file": duplicate,
                "error": "Duplicado detectado (verificación previa)",
                "duplicate_info": {
                    "is_duplicate": True,
                    "reason": "Archivo ya existe en la base de datos",
                    "message": "Este archivo ya ha sido procesado anteriormente"
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

@app.post("/upload-folder/", response_model=schemas.BulkUploadResponse)
async def upload_folder_books(
    folder_path: str,
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una carpeta específica del sistema
    """
    # Verificar que Google Drive esté configurado
    try:
        from google_drive_manager import drive_manager
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
            "duplicate_files": duplicates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante la carga de carpeta: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la carga de carpeta: {str(e)}")

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



@app.get("/drive/status")
def check_drive_status():
    """
    Verifica el estado de Google Drive
    """
    try:
        from google_drive_manager import drive_manager
        
        if not drive_manager.service:
            return {
                "status": "not_configured",
                "message": "Google Drive no está configurado",
                "setup_required": True
            }
        
        # Verificar conexión intentando obtener información de almacenamiento
        storage_info = drive_manager.get_storage_info()
        if storage_info:
            return {
                "status": "ok",
                "message": "Google Drive está funcionando correctamente",
                "storage_info": storage_info,
                "setup_required": False
            }
        else:
            return {
                "status": "error",
                "message": "No se pudo obtener información de Google Drive",
                "setup_required": False
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar Google Drive: {str(e)}",
            "error_type": type(e).__name__,
            "setup_required": True
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
