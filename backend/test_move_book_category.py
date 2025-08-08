#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de mover libros entre categorías en Google Drive
"""

import os
import sys
import logging
from sqlalchemy.orm import Session

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import crud
from google_drive_manager import get_drive_manager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_move_book_category():
    """
    Prueba la funcionalidad de mover un libro entre categorías
    """
    try:
        # Obtener conexión a la base de datos
        db = SessionLocal()
        
        # Obtener el gestor de Google Drive
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            logger.error("❌ Google Drive no está configurado")
            return False
        
        # Buscar un libro que esté en Google Drive
        books = db.query(crud.models.Book).filter(
            crud.models.Book.drive_file_id.isnot(None)
        ).limit(1).all()
        
        if not books:
            logger.error("❌ No se encontraron libros en Google Drive para probar")
            return False
        
        book = books[0]
        logger.info(f"📖 Libro encontrado para prueba: {book.title} (ID: {book.id})")
        logger.info(f"📍 Categoría actual: {book.category}")
        logger.info(f"🔗 ID de Google Drive: {book.drive_file_id}")
        
        # Probar mover a una nueva categoría
        new_category = "Categoría de Prueba"
        
        logger.info(f"🔄 Intentando mover libro a categoría: {new_category}")
        
        # Llamar a la función de movimiento
        result = drive_manager.move_book_to_new_category(
            file_id=book.drive_file_id,
            new_category=new_category,
            title=book.title,
            author=book.author
        )
        
        if result['success']:
            logger.info(f"✅ Libro movido exitosamente: {result['message']}")
            
            # Actualizar la base de datos
            book.category = new_category
            if 'web_view_link' in result:
                book.drive_web_link = result['web_view_link']
            if 'letter_folder' in result:
                book.drive_letter_folder = result['letter_folder']
            
            db.commit()
            logger.info(f"✅ Base de datos actualizada")
            
            # Mover de vuelta a la categoría original
            logger.info(f"🔄 Moviendo de vuelta a categoría original: {book.category}")
            original_category = "Psicología"  # O la categoría que prefieras
            
            result_back = drive_manager.move_book_to_new_category(
                file_id=book.drive_file_id,
                new_category=original_category,
                title=book.title,
                author=book.author
            )
            
            if result_back['success']:
                logger.info(f"✅ Libro movido de vuelta exitosamente: {result_back['message']}")
                
                # Actualizar la base de datos de vuelta
                book.category = original_category
                if 'web_view_link' in result_back:
                    book.drive_web_link = result_back['web_view_link']
                if 'letter_folder' in result_back:
                    book.drive_letter_folder = result_back['letter_folder']
                
                db.commit()
                logger.info(f"✅ Base de datos actualizada de vuelta")
                
                return True
            else:
                logger.error(f"❌ Error al mover de vuelta: {result_back['error']}")
                return False
        else:
            logger.error(f"❌ Error al mover libro: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
        return False
    finally:
        db.close()

def test_update_book_endpoint():
    """
    Prueba el endpoint de actualización de libros
    """
    try:
        # Obtener conexión a la base de datos
        db = SessionLocal()
        
        # Buscar un libro que esté en Google Drive
        books = db.query(crud.models.Book).filter(
            crud.models.Book.drive_file_id.isnot(None)
        ).limit(1).all()
        
        if not books:
            logger.error("❌ No se encontraron libros en Google Drive para probar")
            return False
        
        book = books[0]
        logger.info(f"📖 Libro encontrado para prueba de endpoint: {book.title} (ID: {book.id})")
        logger.info(f"📍 Categoría actual: {book.category}")
        
        # Simular la actualización del endpoint
        old_category = book.category
        new_category = "Categoría de Prueba Endpoint"
        
        logger.info(f"🔄 Simulando actualización de categoría: {old_category} -> {new_category}")
        
        # Actualizar la categoría
        book.category = new_category
        
        # Verificar si el libro está en Google Drive y se cambió la categoría
        if (book.drive_file_id and old_category and new_category != old_category):
            try:
                # Importar el gestor de Google Drive
                from google_drive_manager import get_drive_manager
                drive_manager = get_drive_manager()
                
                if not drive_manager.service:
                    logger.warning("⚠️ Google Drive no está configurado, actualizando solo la base de datos")
                else:
                    # Mover el archivo a la nueva categoría en Google Drive
                    move_result = drive_manager.move_book_to_new_category(
                        file_id=book.drive_file_id,
                        new_category=new_category,
                        title=book.title,
                        author=book.author
                    )
                    
                    if move_result['success']:
                        logger.info(f"✅ Libro movido exitosamente en Google Drive: {book.title} -> {new_category}")
                        # Actualizar información adicional si es necesario
                        if 'web_view_link' in move_result:
                            book.drive_web_link = move_result['web_view_link']
                        if 'letter_folder' in move_result:
                            book.drive_letter_folder = move_result['letter_folder']
                    else:
                        logger.error(f"❌ Error al mover libro en Google Drive: {move_result['error']}")
                        
            except Exception as drive_error:
                logger.error(f"❌ Error al procesar movimiento en Google Drive: {drive_error}")
        
        db.commit()
        logger.info(f"✅ Prueba de endpoint completada")
        
        # Mover de vuelta a la categoría original
        book.category = old_category
        db.commit()
        logger.info(f"✅ Categoría restaurada")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en la prueba del endpoint: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 Iniciando pruebas de funcionalidad de mover libros entre categorías")
    
    # Prueba 1: Función directa de movimiento
    logger.info("\n" + "="*50)
    logger.info("PRUEBA 1: Función directa de movimiento")
    logger.info("="*50)
    
    if test_move_book_category():
        logger.info("✅ Prueba 1 completada exitosamente")
    else:
        logger.error("❌ Prueba 1 falló")
    
    # Prueba 2: Simulación del endpoint
    logger.info("\n" + "="*50)
    logger.info("PRUEBA 2: Simulación del endpoint")
    logger.info("="*50)
    
    if test_update_book_endpoint():
        logger.info("✅ Prueba 2 completada exitosamente")
    else:
        logger.error("❌ Prueba 2 falló")
    
    logger.info("\n🎯 Pruebas completadas")
