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

import crud, models, database, schemas

# --- Configuración Inicial ---
load_dotenv(dotenv_path='../.env')
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY: raise Exception("No se encontró la GEMINI_API_KEY.")
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
    Devuelve ÚNICAMENTE un objeto JSON con las claves "title", "author" y "category".
    Si no puedes determinar un valor, usa "Desconocido".
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
            if match.startswith("```json"):
                match = match[7:]
            if match.endswith("```"):
                match = match[:-3]
            
            result = json.loads(match.strip())
            
            # Validar que el resultado tenga las claves esperadas
            if not all(key in result for key in ["title", "author", "category"]):
                raise ValueError("Respuesta de IA incompleta")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error de JSON en intento {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {"title": "Error de formato", "author": "Error de formato", "category": "Error de formato"}
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
                return {"title": "Error de IA", "author": "Error de IA", "category": "Error de IA"}
    
    return {"title": "Error de IA", "author": "Error de IA", "category": "Error de IA"}

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
    allow_origins=["http://localhost:3000"],
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
    books_dir = "books"
    os.makedirs(books_dir, exist_ok=True)
    file_path = os.path.abspath(os.path.join(books_dir, book_file.filename))

    if crud.get_book_by_path(db, file_path):
        raise HTTPException(status_code=409, detail="Este libro ya ha sido añadido.")

    with open(file_path, "wb") as buffer: shutil.copyfileobj(book_file.file, buffer)

    file_ext = os.path.splitext(book_file.filename)[1].lower()
    try:
        if file_ext == ".pdf": book_data = process_pdf(file_path, STATIC_COVERS_DIR)
        elif file_ext == ".epub": book_data = process_epub(file_path, STATIC_COVERS_DIR)
        else: raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")
    except HTTPException as e:
        os.remove(file_path) # Limpiar el archivo subido si el procesamiento falla
        raise e

    gemini_result = analyze_with_gemini(book_data["text"])
    
    # --- Puerta de Calidad ---
    title = gemini_result.get("title", "Desconocido")
    author = gemini_result.get("author", "Desconocido")

    if title == "Desconocido" and author == "Desconocido":
        os.remove(file_path) # Borrar el archivo que no se pudo analizar
        raise HTTPException(status_code=422, detail="La IA no pudo identificar el título ni el autor del libro. No se ha añadido.")

    return crud.create_book(
        db=db, 
        title=title, 
        author=author, 
        category=gemini_result.get("category", "Desconocido"), 
        cover_image_url=book_data.get("cover_image_url"), 
        file_path=file_path
    )

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
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    
    # Verificar si el archivo existe
    if not os.path.exists(book.file_path):
        # Si el archivo no existe, podría ser un libro extraído de un ZIP
        # Intentar buscar el archivo en el directorio de libros
        books_dir = "books"
        filename = os.path.basename(book.file_path)
        
        # Buscar archivos que coincidan con el nombre (ignorando el timestamp)
        if os.path.exists(books_dir):
            for file in os.listdir(books_dir):
                if file.endswith(filename) or filename in file:
                    book.file_path = os.path.abspath(os.path.join(books_dir, file))
                    break
        
        # Si aún no se encuentra, reportar error
        if not os.path.exists(book.file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Archivo no encontrado en el disco. Ruta: {book.file_path}"
            )

    file_ext = os.path.splitext(book.file_path)[1].lower()
    filename = os.path.basename(book.file_path)
    
    if file_ext == ".pdf":
        return FileResponse(
            path=book.file_path,
            filename=filename,
            media_type='application/pdf',
            content_disposition_type='inline'
        )
    else: # Para EPUB y otros tipos de archivo
        return FileResponse(
            path=book.file_path,
            filename=filename,
            media_type='application/epub+zip',
            content_disposition_type='attachment'
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

def extract_books_from_zip(zip_path: str, temp_dir: str) -> List[str]:
    """Extrae libros de un archivo ZIP y retorna las rutas de los libros encontrados"""
    extracted_books = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraer el ZIP a un subdirectorio temporal
            zip_name = Path(zip_path).stem
            extract_dir = os.path.join(temp_dir, f"extracted_{zip_name}")
            os.makedirs(extract_dir, exist_ok=True)
            
            zip_ref.extractall(extract_dir)
            
            # Buscar archivos PDF y EPUB en el contenido extraído
            for extracted_file in Path(extract_dir).rglob('*'):
                if extracted_file.is_file() and extracted_file.suffix.lower() in {'.pdf', '.epub'}:
                    extracted_books.append(str(extracted_file))
                    
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

async def process_single_book_async(file_path: str, static_dir: str, db: Session) -> dict:
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
        
        # Verificar si el archivo proviene de un ZIP temporal (extraído)
        is_from_temp_zip = "extracted_" in file_path or "temp" in file_path
        
        # Si el archivo proviene de un ZIP temporal, copiarlo a un directorio permanente
        if is_from_temp_zip:
            books_dir = "books"
            os.makedirs(books_dir, exist_ok=True)
            
            # Generar un nombre único para el archivo
            original_filename = Path(file_path).name
            unique_filename = f"{int(time.time())}_{original_filename}"
            permanent_path = os.path.abspath(os.path.join(books_dir, unique_filename))
            
            # Copiar el archivo al directorio permanente
            shutil.copy2(file_path, permanent_path)
            file_path = permanent_path
        
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
        
        # Guardar en base de datos
        book_result = crud.create_book_with_duplicate_check(
            db=db,
            title=analysis["title"],
            author=analysis["author"],
            category=analysis["category"],
            cover_image_url=result.get("cover_image_url"),
            file_path=file_path
        )
        
        if book_result["success"]:
            return {
                "success": True,
                "file": file_path,
                "book": {
                    "id": book_result["book"].id,
                    "title": book_result["book"].title,
                    "author": book_result["book"].author,
                    "category": book_result["book"].category
                }
            }
        else:
            return {
                "success": False,
                "file": file_path,
                "error": "Error al guardar en base de datos",
                "duplicate_info": book_result["duplicate_info"]
            }
        
    except Exception as e:
        return {
            "success": False,
            "file": file_path,
            "error": str(e)
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
    
    try:
        # Crear directorio temporal para extraer el ZIP
        with tempfile.TemporaryDirectory() as temp_dir:
            # Leer y extraer el ZIP
            zip_content = await folder_zip.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Encontrar todos los archivos de libros y ZIPs que contengan libros
            all_files = find_book_files(temp_dir)
            
            # Separar archivos directos de libros y ZIPs
            direct_books = [f for f in all_files if Path(f).suffix.lower() in {'.pdf', '.epub'}]
            zip_files = [f for f in all_files if Path(f).suffix.lower() == '.zip']
            
            # Procesar ZIPs que contengan libros
            books_from_zips = []
            for zip_file in zip_files:
                extracted_books = process_zip_containing_books(zip_file, temp_dir)
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
                    "file": duplicate["file"],
                    "error": "Duplicado detectado (verificación previa)",
                    "duplicate_info": {
                        "is_duplicate": True,
                        "reason": duplicate["reason"],
                        "existing_book": {
                            "id": duplicate["existing_book"].id,
                            "title": duplicate["existing_book"].title,
                            "author": duplicate["existing_book"].author,
                            "category": duplicate["existing_book"].category
                        } if duplicate["existing_book"] else None,
                        "message": duplicate["message"]
                    }
                })
            
            # Resumen de resultados
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"] and "Duplicado detectado" not in r.get("error", "")]
            duplicates = [r for r in results if "Duplicado detectado" in r.get("error", "")]
            
            # Información de optimización
            optimization_info = f"🚀 Optimización: Se ahorraron {stats['saved_ai_calls']} llamadas a IA detectando {stats['duplicate_files']} duplicados en verificación previa."
            
            return {
                "message": f"Procesamiento completado. {len(successful)} libros procesados exitosamente, {len(failed)} fallaron, {len(duplicates)} duplicados detectados. {optimization_info}",
                "total_files": len(book_files),
                "successful": len(successful),
                "failed": len(failed),
                "duplicates": len(duplicates),
                "successful_books": successful,
                "failed_files": failed,
                "duplicate_files": duplicates,
                "optimization_stats": stats
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la carga masiva: {str(e)}")

@app.post("/upload-folder/", response_model=schemas.BulkUploadResponse)
async def upload_folder_books(
    folder_path: str,
    db: Session = Depends(get_db)
):
    """
    Carga masiva de libros desde una ruta de carpeta local
    """
    try:
        # Verificar que la carpeta existe
        if not Path(folder_path).exists():
            raise HTTPException(status_code=400, detail="La carpeta especificada no existe.")
        
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
        max_workers = min(4, len(book_files))  # Máximo 4 workers concurrentes
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
        failed = [r for r in results if not r["success"] and r.get("error") != "Duplicado detectado"]
        duplicates = [r for r in results if not r["success"] and r.get("error") == "Duplicado detectado"]
        
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la carga masiva: {str(e)}")

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
        
        if "Error de IA" in test_result["title"]:
            return {
                "status": "error",
                "message": "La API de IA no está respondiendo correctamente",
                "test_result": test_result
            }
        else:
            return {
                "status": "ok",
                "message": "La API de IA está funcionando correctamente",
                "test_result": test_result
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar la API de IA: {str(e)}",
            "error_type": type(e).__name__
        }
