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

def get_book(db: Session, book_id: int):
    """Obtiene un libro por su ID"""
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_book_by_filename(db: Session, filename: str):
    """Busca un libro por el nombre del archivo"""
    return db.query(models.Book).filter(
        or_(
            models.Book.file_path.like(f"%{filename}"),
            models.Book.drive_filename == filename
        )
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
    
    # Verificar por drive_file_id si se proporciona (para evitar duplicados en Google Drive)
    if file_path:
        # Buscar por drive_filename también
        filename = Path(file_path).name
        existing_by_drive_filename = db.query(models.Book).filter(
            models.Book.drive_filename == filename
        ).first()
        if existing_by_drive_filename:
            return {
                "is_duplicate": True,
                "reason": "drive_filename",
                "existing_book": existing_by_drive_filename,
                "message": f"Ya existe un libro con el mismo nombre en Google Drive: {filename}"
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
    
    books = query.order_by(desc(models.Book.id)).all()
    
    # Agregar información de source a cada libro
    books_with_source = []
    for book in books:
        # Determinar el source basado en la presencia de drive_file_id y synced_to_drive
        if book.drive_file_id and book.synced_to_drive:
            source = 'drive'
        elif book.drive_file_id and not book.synced_to_drive:
            source = 'drive'  # Si tiene drive_file_id pero no está sincronizado, aún está en drive
        else:
            source = 'local'  # Si no tiene drive_file_id, está local
        
        book_dict = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'category': book.category,
            'cover_image_url': book.cover_image_url,
            'file_path': book.file_path,
            'drive_file_id': book.drive_file_id,
            'drive_web_link': book.drive_web_link,
            'drive_letter_folder': book.drive_letter_folder,
            'drive_filename': book.drive_filename,
            'synced_to_drive': book.synced_to_drive,
            'upload_date': book.upload_date.isoformat() if book.upload_date else None,
            'source': source
        }
        books_with_source.append(book_dict)
    
    return books_with_source

def get_categories(db: Session) -> list[str]:
    return [c[0] for c in db.query(models.Book.category).distinct().order_by(models.Book.category).all()]

def create_book(db: Session, title: str, author: str, category: str, cover_image_url: str, drive_info: dict, file_path: str = None):
    """
    Crea un libro en la base de datos con Google Drive como almacenamiento principal
    """
    if not drive_info or not drive_info.get('id'):
        raise ValueError("Se requiere información de Google Drive para crear el libro")
    
    db_book = models.Book(
        title=title,
        author=author,
        category=category,
        cover_image_url=cover_image_url,
        file_path=file_path,  # Opcional, solo para archivos temporales
        drive_file_id=drive_info['id'],
        drive_web_link=drive_info.get('web_view_link'),
        drive_letter_folder=drive_info.get('letter_folder'),
        drive_filename=drive_info.get('filename')
    )
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def create_local_book(db: Session, title: str, author: str, category: str, cover_image_url: str, file_path: str):
    """
    Crea un libro local en la base de datos sin Google Drive
    """
    if not file_path:
        raise ValueError("Se requiere una ruta de archivo para crear un libro local")
    
    db_book = models.Book(
        title=title,
        author=author,
        category=category,
        cover_image_url=cover_image_url,
        file_path=file_path,
        drive_file_id=None,
        drive_web_link=None,
        drive_letter_folder=None,
        drive_filename=None,
        synced_to_drive=False
    )
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def create_book_with_duplicate_check(db: Session, title: str, author: str, category: str, cover_image_url: str, drive_info: dict = None, file_path: str = None):
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
        # Determinar si es un libro local o de Google Drive
        if drive_info and drive_info.get('id'):
            # Libro de Google Drive
            db_book = create_book(db, title, author, category, cover_image_url, drive_info, file_path)
        elif file_path:
            # Libro local
            db_book = create_local_book(db, title, author, category, cover_image_url, file_path)
        else:
            raise ValueError("Se requiere información de Google Drive o una ruta de archivo local para crear el libro")
        
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
    Elimina un libro de Google Drive y limpia archivos temporales locales.
    Retorna el libro eliminado o None si no se encontró.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return None
    
    try:
        # Eliminar de Google Drive (obligatorio)
        if book.drive_file_id:
            try:
                from google_drive_manager import get_drive_manager
                drive_manager = get_drive_manager()
                if drive_manager.service:
                    result = drive_manager.delete_book_from_drive(book.drive_file_id)
                    if result['success']:
                        logger.info(f"Libro eliminado de Google Drive: {book.title}")
                    else:
                        logger.warning(f"No se pudo eliminar de Google Drive: {book.title} - {result['error']}")
                else:
                    logger.warning("Google Drive no está configurado")
            except Exception as e:
                logger.warning(f"Error al eliminar de Google Drive: {e}")
        else:
            logger.warning(f"Libro sin ID de Google Drive: {book.title}")
        
        # Eliminar portada de Google Drive si existe
        if book.cover_image_url and book.cover_image_url.startswith('http'):
            try:
                from google_drive_manager import get_drive_manager
                drive_manager = get_drive_manager()
                if drive_manager.service:
                    cover_result = drive_manager.delete_cover_from_drive(book.cover_image_url)
                    if cover_result['success']:
                        logger.info(f"Portada eliminada de Google Drive: {book.title}")
                    else:
                        logger.warning(f"No se pudo eliminar portada de Google Drive: {book.title} - {cover_result['error']}")
                else:
                    logger.warning("Google Drive no está configurado para eliminar portada")
            except Exception as e:
                logger.warning(f"Error al eliminar portada de Google Drive: {e}")
        
        # Limpiar archivo temporal local si existe
        if book.file_path and os.path.exists(book.file_path):
            try:
                os.remove(book.file_path)
                logger.info(f"Archivo temporal eliminado: {book.file_path}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar el archivo temporal {book.file_path}: {e}")
        
        # Eliminar imagen de portada local si existe
        if book.cover_image_url and os.path.exists(book.cover_image_url):
            try:
                os.remove(book.cover_image_url)
                logger.info(f"Imagen de portada eliminada: {book.cover_image_url}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar la imagen de portada {book.cover_image_url}: {e}")
        
        # Eliminar de la base de datos
        db.delete(book)
        db.commit()
        logger.info(f"Libro eliminado de la base de datos: {book.title}")
        
        return book
        
    except Exception as e:
        logger.error(f"Error al eliminar libro {book_id}: {e}")
        db.rollback()
        return None

def delete_books_by_category(db: Session, category: str):
    """
    Elimina todos los libros de una categoría específica de Google Drive.
    Retorna el número de libros eliminados.
    """
    books_to_delete = db.query(models.Book).filter(models.Book.category == category).all()
    if not books_to_delete:
        return 0
    
    deleted_count = 0
    
    try:
        for book in books_to_delete:
            # Eliminar de Google Drive (obligatorio)
            if book.drive_file_id:
                try:
                    from google_drive_manager import get_drive_manager
                    drive_manager = get_drive_manager()
                    if drive_manager.service:
                        result = drive_manager.delete_book_from_drive(book.drive_file_id)
                        if result['success']:
                            logger.info(f"Libro eliminado de Google Drive: {book.title}")
                        else:
                            logger.warning(f"No se pudo eliminar de Google Drive: {book.title} - {result['error']}")
                    else:
                        logger.warning("Google Drive no está configurado")
                except Exception as e:
                    logger.warning(f"Error al eliminar de Google Drive: {e}")
            else:
                logger.warning(f"Libro sin ID de Google Drive: {book.title}")
            
            # Eliminar portada de Google Drive si existe
            if book.cover_image_url and book.cover_image_url.startswith('http'):
                try:
                    from google_drive_manager import get_drive_manager
                    drive_manager = get_drive_manager()
                    if drive_manager.service:
                        cover_result = drive_manager.delete_cover_from_drive(book.cover_image_url)
                        if cover_result['success']:
                            logger.info(f"Portada eliminada de Google Drive: {book.title}")
                        else:
                            logger.warning(f"No se pudo eliminar portada de Google Drive: {book.title} - {cover_result['error']}")
                    else:
                        logger.warning("Google Drive no está configurado para eliminar portada")
                except Exception as e:
                    logger.warning(f"Error al eliminar portada de Google Drive: {e}")
            
            # Limpiar archivo temporal local si existe
            if book.file_path and os.path.exists(book.file_path):
                try:
                    os.remove(book.file_path)
                    logger.info(f"Archivo temporal eliminado: {book.file_path}")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal {book.file_path}: {e}")
            
            # Eliminar imagen de portada local si existe
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

def update_book_sync_status(db: Session, book_id: int, synced_to_drive: bool, drive_file_id: str = None, remove_local_file: bool = False):
    """
    Actualiza el estado de sincronización de un libro con Google Drive
    """
    try:
        book = db.query(models.Book).filter(models.Book.id == book_id).first()
        if not book:
            logger.error(f"Libro no encontrado para actualizar estado de sincronización: {book_id}")
            return None
        
        book.synced_to_drive = synced_to_drive
        if drive_file_id:
            book.drive_file_id = drive_file_id
        
        # Si se debe eliminar el archivo local, limpiar la ruta
        if remove_local_file:
            book.file_path = None
            logger.info(f"Ruta de archivo local limpiada para el libro: {book.title}")
        
        db.commit()
        logger.info(f"Estado de sincronización actualizado para el libro: {book.title}")
        
        return book
        
    except Exception as e:
        logger.error(f"Error al actualizar estado de sincronización del libro {book_id}: {e}")
        db.rollback()
        return None

def get_book_by_drive_file_id(db: Session, drive_file_id: str):
    """
    Busca un libro por su drive_file_id
    """
    return db.query(models.Book).filter(models.Book.drive_file_id == drive_file_id).first()

def update_book_drive_info(db: Session, book_id: int, drive_file_id: str = None, synced_to_drive: bool = False):
    """
    Actualiza la información de Google Drive de un libro
    """
    try:
        book = db.query(models.Book).filter(models.Book.id == book_id).first()
        if not book:
            logger.error(f"Libro no encontrado para actualizar información de Drive: {book_id}")
            return None
        
        # Si drive_file_id es None, limpiar el campo
        if drive_file_id is None:
            book.drive_file_id = None
        else:
            book.drive_file_id = drive_file_id
            
        book.synced_to_drive = synced_to_drive
        
        db.commit()
        logger.info(f"Información de Drive actualizada para el libro: {book.title}")
        
        return book
        
    except Exception as e:
        logger.error(f"Error al actualizar información de Drive del libro {book_id}: {e}")
        db.rollback()
        return None

def get_drive_books(db: Session, category: str | None = None, search: str | None = None):
    """
    Obtiene libros de la base de datos que están en Google Drive
    """
    try:
        # Filtrar libros que están en Google Drive (tienen drive_file_id)
        query = db.query(models.Book).filter(
            models.Book.drive_file_id.isnot(None)
        )
        
        # Aplicar filtro de categoría si se proporciona
        if category:
            query = query.filter(models.Book.category == category)
        
        # Aplicar filtro de búsqueda si se proporciona
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                (models.Book.title.ilike(search_lower)) |
                (models.Book.author.ilike(search_lower)) |
                (models.Book.category.ilike(search_lower))
            )
        
        # Ordenar por fecha de carga (más recientes primero)
        books = query.order_by(models.Book.upload_date.desc()).all()
        
        # Convertir a diccionarios
        books_dict = []
        for book in books:
            book_dict = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'category': book.category,
                'cover_image_url': book.cover_image_url,
                'file_path': book.file_path,
                'drive_file_id': book.drive_file_id,
                'drive_web_link': book.drive_web_link,
                'drive_letter_folder': book.drive_letter_folder,
                'drive_filename': book.drive_filename,
                'synced_to_drive': book.synced_to_drive,
                'upload_date': book.upload_date.isoformat() if book.upload_date else None,
                'source': 'drive'
            }
            books_dict.append(book_dict)
        
        logger.info(f"Obtenidos {len(books_dict)} libros de Google Drive")
        return books_dict
        
    except Exception as e:
        logger.error(f"Error al obtener libros de Google Drive: {e}")
        return []
