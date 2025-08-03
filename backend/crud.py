from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import models
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_book_by_path(db: Session, file_path: str):
    return db.query(models.Book).filter(models.Book.file_path == file_path).first()

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

def delete_book(db: Session, book_id: int):
    """
    Elimina un libro y sus archivos asociados de forma segura.
    Retorna el libro eliminado o None si no se encontró.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return None
    
    try:
        # Eliminar archivo del libro
        if book.file_path and os.path.exists(book.file_path):
            try:
                os.remove(book.file_path)
                logger.info(f"Archivo del libro eliminado: {book.file_path}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar el archivo del libro {book.file_path}: {e}")
        
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
    try:
        for book in books_to_delete:
            # Eliminar archivo del libro
            if book.file_path and os.path.exists(book.file_path):
                try:
                    os.remove(book.file_path)
                    logger.info(f"Archivo del libro eliminado: {book.file_path}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar el archivo del libro {book.file_path}: {e}")
            
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
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error al eliminar libros de la categoría '{category}': {e}")
        db.rollback()
        raise
