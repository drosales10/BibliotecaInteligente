from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import models
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_book_by_path(db: Session, file_path: str):
    return db.query(models.Book).filter(models.Book.file_path == file_path).first()

def get_book_by_filename(db: Session, filename: str):
    """Busca un libro por el nombre del archivo"""
    return db.query(models.Book).filter(
        models.Book.file_path.like(f"%{filename}")
    ).first()

def get_book_by_title_author(db: Session, title: str, author: str):
    """Busca un libro por título y autor (comparación exacta)"""
    return db.query(models.Book).filter(
        models.Book.title == title,
        models.Book.author == author
    ).first()

def get_book_by_title_author_fuzzy(db: Session, title: str, author: str):
    """Busca un libro por título y autor (comparación aproximada)"""
    return db.query(models.Book).filter(
        or_(
            models.Book.title.ilike(f"%{title}%"),
            models.Book.title.ilike(f"%{title.replace(' ', '%')}%")
        ),
        or_(
            models.Book.author.ilike(f"%{author}%"),
            models.Book.author.ilike(f"%{author.replace(' ', '%')}%")
        )
    ).first()

def is_duplicate_book(db: Session, title: str, author: str, file_path: str = None) -> dict:
    """
    Verifica si un libro es un duplicado basándose en múltiples criterios.
    Retorna un diccionario con información sobre el duplicado encontrado.
    """
    # Verificar por nombre de archivo si se proporciona
    if file_path:
        filename = Path(file_path).name
        existing_by_filename = get_book_by_filename(db, filename)
        if existing_by_filename:
            return {
                "is_duplicate": True,
                "reason": "filename",
                "existing_book": existing_by_filename,
                "message": f"Ya existe un libro con el mismo nombre de archivo: {filename}"
            }
    
    # Verificar por título y autor exacto
    existing_exact = get_book_by_title_author(db, title, author)
    if existing_exact:
        return {
            "is_duplicate": True,
            "reason": "title_author_exact",
            "existing_book": existing_exact,
            "message": f"Ya existe un libro con el mismo título y autor: '{title}' por {author}"
        }
    
    # Verificar por título y autor aproximado (fuzzy matching)
    existing_fuzzy = get_book_by_title_author_fuzzy(db, title, author)
    if existing_fuzzy:
        return {
            "is_duplicate": True,
            "reason": "title_author_fuzzy",
            "existing_book": existing_fuzzy,
            "message": f"Posible duplicado encontrado: '{existing_fuzzy.title}' por {existing_fuzzy.author}"
        }
    
    return {
        "is_duplicate": False,
        "reason": None,
        "existing_book": None,
        "message": "No se encontraron duplicados"
    }

def get_books(db: Session, category: str | None = None, search: str | None = None):
    query = db.query(models.Book)
    if category:
        query = query.filter(models.Book.category == category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Book.title.ilike(search_term),
                models.Book.author.ilike(search_term),
                models.Book.category.ilike(search_term)
            )
        )
    return query.order_by(desc(models.Book.id)).all()

def get_categories(db: Session) -> list[str]:
    return [c[0] for c in db.query(models.Book.category).distinct().order_by(models.Book.category).all()]

def create_book(db: Session, title: str, author: str, category: str, cover_image_url: str, file_path: str):
    db_book = models.Book(
        title=title,
        author=author,
        category=category,
        cover_image_url=cover_image_url,
        file_path=file_path
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def create_book_with_duplicate_check(db: Session, title: str, author: str, category: str, cover_image_url: str, file_path: str):
    """
    Crea un libro verificando duplicados primero.
    Retorna el libro creado o información sobre el duplicado encontrado.
    """
    # Verificar duplicados
    duplicate_check = is_duplicate_book(db, title, author, file_path)
    
    if duplicate_check["is_duplicate"]:
        return {
            "success": False,
            "duplicate_info": duplicate_check,
            "book": None
        }
    
    # Si no es duplicado, crear el libro
    try:
        db_book = create_book(db, title, author, category, cover_image_url, file_path)
        return {
            "success": True,
            "duplicate_info": None,
            "book": db_book
        }
    except Exception as e:
        logger.error(f"Error al crear libro: {e}")
        return {
            "success": False,
            "duplicate_info": {"message": f"Error al crear libro: {str(e)}"},
            "book": None
        }

def delete_book(db: Session, book_id: int):
    """
    Elimina un libro y sus archivos asociados de forma segura.
    Retorna el libro eliminado o None si no se encontró.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return None
    
    try:
        # Guardar la ruta del archivo y su directorio para limpieza posterior
        file_path = book.file_path
        file_dir = None
        
        # Eliminar archivo del libro
        if file_path and os.path.exists(file_path):
            try:
                # Obtener el directorio del archivo antes de eliminarlo
                file_dir = os.path.dirname(file_path)
                os.remove(file_path)
                logger.info(f"Archivo del libro eliminado: {file_path}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar el archivo del libro {file_path}: {e}")
        
        # Eliminar imagen de portada
        if book.cover_image_url and os.path.exists(book.cover_image_url):
            try:
                os.remove(book.cover_image_url)
                logger.info(f"Imagen de portada eliminada: {book.cover_image_url}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar la imagen de portada {book.cover_image_url}: {e}")
        
        # Eliminar registro de la base de datos
        db.delete(book)
        db.commit()
        logger.info(f"Libro '{book.title}' eliminado exitosamente de la base de datos")
        
        # Limpiar directorio vacío si es un directorio de extracción de ZIP
        if file_dir and "books" in file_dir and os.path.exists(file_dir):
            try:
                # Verificar si el directorio está vacío
                if not os.listdir(file_dir):
                    os.rmdir(file_dir)
                    logger.info(f"Directorio vacío eliminado: {file_dir}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar el directorio {file_dir}: {e}")
        
        return book
        
    except Exception as e:
        logger.error(f"Error al eliminar el libro {book_id}: {e}")
        db.rollback()
        raise

def delete_books_by_category(db: Session, category: str):
    """
    Elimina todos los libros de una categoría específica.
    Retorna el número de libros eliminados.
    """
    books_to_delete = db.query(models.Book).filter(models.Book.category == category).all()
    if not books_to_delete:
        return 0
    
    deleted_count = 0
    directories_to_check = set()  # Para rastrear directorios que podrían quedar vacíos
    
    try:
        for book in books_to_delete:
            # Guardar la ruta del archivo y su directorio para limpieza posterior
            file_path = book.file_path
            file_dir = None
            
            # Eliminar archivo del libro
            if file_path and os.path.exists(file_path):
                try:
                    # Obtener el directorio del archivo antes de eliminarlo
                    file_dir = os.path.dirname(file_path)
                    if file_dir and "books" in file_dir:
                        directories_to_check.add(file_dir)
                    os.remove(file_path)
                    logger.info(f"Archivo del libro eliminado: {file_path}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar el archivo del libro {file_path}: {e}")
            
            # Eliminar imagen de portada
            if book.cover_image_url and os.path.exists(book.cover_image_url):
                try:
                    os.remove(book.cover_image_url)
                    logger.info(f"Imagen de portada eliminada: {book.cover_image_url}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar la imagen de portada {book.cover_image_url}: {e}")
            
            db.delete(book)
            deleted_count += 1
        
        db.commit()
        logger.info(f"Categoría '{category}' eliminada con {deleted_count} libros")
        
        # Limpiar directorios vacíos después de eliminar todos los libros
        for directory in directories_to_check:
            if os.path.exists(directory):
                try:
                    # Verificar si el directorio está vacío
                    if not os.listdir(directory):
                        os.rmdir(directory)
                        logger.info(f"Directorio vacío eliminado: {directory}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar el directorio {directory}: {e}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error al eliminar libros de la categoría '{category}': {e}")
        db.rollback()
        raise
