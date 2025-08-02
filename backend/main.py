from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
import fitz
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import List

import crud, models, database, schemas

# --- Configuración Inicial ---
load_dotenv(dotenv_path='../.env')
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY: raise Exception("No se encontró la GEMINI_API_KEY.")
genai.configure(api_key=API_KEY)
models.Base.metadata.create_all(bind=database.engine)

# --- Funciones de IA y Procesamiento ---
def analyze_with_gemini(text: str) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Eres un bibliotecario experto. Analiza el siguiente texto extraído de las primeras páginas de un libro.
    Tu tarea es identificar el título, el autor y la categoría principal del libro.
    Devuelve ÚNICAMENTE un objeto JSON con las claves "title", "author" y "category".
    Si no puedes determinar un valor, usa "Desconocido".
    Ejemplo: {{\"title\": \"El nombre del viento\", \"author\": \"Patrick Rothfuss\", \"category\": \"Fantasía\"}}
    Texto a analizar: --- {text[:4000]} ---
    """
    try:
        response = model.generate_content(prompt)
        match = response.text.strip()
        if match.startswith("```json"): match = match[7:]
        if match.endswith("```"): match = match[:-3]
        return json.loads(match.strip())
    except Exception as e:
        print(f"Error al analizar con Gemini: {e}")
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
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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

@app.delete("/books/{book_id}")
def delete_single_book(book_id: int, db: Session = Depends(get_db)):
    book = crud.delete_book(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    return {"message": f"Libro '{book.title}' eliminado con éxito."}

@app.delete("/categories/{category_name}")
def delete_category_and_books(category_name: str, db: Session = Depends(get_db)):
    deleted_count = crud.delete_books_by_category(db, category=category_name)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Categoría '{category_name}' no encontrada o ya está vacía.")
    return {"message": f"Categoría '{category_name}' y sus {deleted_count} libros han sido eliminados."}

@app.get("/books/download/{book_id}")
def download_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book: raise HTTPException(status_code=404, detail="Libro no encontrado.")
    if not os.path.exists(book.file_path): raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path=book.file_path, filename=os.path.basename(book.file_path))