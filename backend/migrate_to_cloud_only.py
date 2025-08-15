#!/usr/bin/env python3
"""
Script para migrar la aplicación a almacenamiento exclusivo en Google Drive
Elimina archivos locales y actualiza la base de datos
"""

import os
import shutil
import sys
from database import SessionLocal
from models import Book
from google_drive_manager import drive_manager

def print_separator(title):
    """Imprime un separador con título"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def check_drive_connection():
    """Verifica la conexión con Google Drive"""
    print_separator("VERIFICANDO CONEXIÓN CON GOOGLE DRIVE")
    
    if not drive_manager.service:
        print("❌ Google Drive no está configurado")
        print("   Ejecuta primero: python setup_google_drive.py")
        return False
    
    try:
        storage_info = drive_manager.get_storage_info()
        if storage_info:
            print("✅ Conexión exitosa con Google Drive")
            print(f"📁 Carpeta raíz: {storage_info['root_folder_name']}")
            print(f"💾 Tamaño actual: {storage_info['total_size_mb']} MB")
            return True
        else:
            print("❌ No se pudo obtener información de Google Drive")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def get_books_with_local_files():
    """Obtiene libros que tienen archivos locales"""
    print_separator("ANALIZANDO LIBROS CON ARCHIVOS LOCALES")
    
    db = SessionLocal()
    try:
        # Obtener libros que tienen file_path
        books = db.query(Book).filter(Book.file_path.isnot(None)).all()
        
        print(f"📚 Total de libros con archivos locales: {len(books)}")
        
        if books:
            print("\n📋 Libros con archivos locales:")
            for i, book in enumerate(books[:10], 1):
                print(f"  {i}. {book.title} - {book.author}")
                print(f"     Archivo: {book.file_path}")
                # Construir ruta completa para verificar existencia
                from main import get_book_file_path
                book_file_path = get_book_file_path(book) if book.file_path else None
                print(f"     Existe: {os.path.exists(book_file_path) if book_file_path else 'N/A'}")
                print()
            
            if len(books) > 10:
                print(f"     ... y {len(books) - 10} libros más")
        
        return books
    finally:
        db.close()

def migrate_book_to_cloud_only(book):
    """Migra un libro individual a almacenamiento exclusivo en la nube"""
    try:
        db = SessionLocal()
        
        # Verificar que el libro esté en Google Drive
        if not book.drive_file_id:
            print(f"⚠️ Libro sin ID de Google Drive: {book.title}")
            return False
        
        # Eliminar archivo local si existe
        if book.file_path:
            # Construir ruta completa para verificar existencia
            from main import get_book_file_path
            book_file_path = get_book_file_path(book)
            if book_file_path and os.path.exists(book_file_path):
                try:
                    os.remove(book_file_path)
                    print(f"🗑️ Archivo local eliminado: {book_file_path}")
                except OSError as e:
                    print(f"⚠️ No se pudo eliminar archivo local: {e}")
        
        # Limpiar imagen de portada local si existe
        if book.cover_image_url and os.path.exists(book.cover_image_url):
            try:
                os.remove(book.cover_image_url)
                print(f"🗑️ Imagen de portada eliminada: {book.cover_image_url}")
            except OSError as e:
                print(f"⚠️ No se pudo eliminar imagen de portada: {e}")
        
        # Actualizar base de datos para marcar como solo en la nube
        book.file_path = None  # Eliminar ruta local
        db.commit()
        print(f"✅ Migrado a nube: {book.title}")
        return True
        
    except Exception as e:
        print(f"❌ Error migrando {book.title}: {e}")
        return False
    finally:
        db.close()

def cleanup_local_directories():
    """Limpia directorios locales que ya no se necesitan"""
    print_separator("LIMPIANDO DIRECTORIOS LOCALES")
    
    directories_to_clean = [
        "books",
        "temp_books", 
        "temp_processing",
        "temp_bulk_upload",
        "temp_downloads"
    ]
    
    cleaned_count = 0
    for directory in directories_to_clean:
        if os.path.exists(directory):
            try:
                # Verificar si el directorio está vacío
                if not os.listdir(directory):
                    os.rmdir(directory)
                    print(f"🗑️ Directorio vacío eliminado: {directory}")
                    cleaned_count += 1
                else:
                    print(f"⚠️ Directorio no vacío (mantener): {directory}")
            except OSError as e:
                print(f"⚠️ No se pudo eliminar directorio {directory}: {e}")
    
    print(f"📊 Directorios limpiados: {cleaned_count}")

def migrate_all_books():
    """Migra todos los libros a almacenamiento exclusivo en la nube"""
    print_separator("INICIANDO MIGRACIÓN A ALMACENAMIENTO EXCLUSIVO EN LA NUBE")
    
    # Verificar conexión
    if not check_drive_connection():
        return
    
    # Obtener libros con archivos locales
    books = get_books_with_local_files()
    
    if not books:
        print("✅ No hay libros para migrar")
        cleanup_local_directories()
        return
    
    # Confirmar migración
    print(f"\n⚠️ ADVERTENCIA: Esta operación eliminará TODOS los archivos locales.")
    print(f"Los libros solo estarán disponibles en Google Drive.")
    print(f"\n¿Deseas continuar con la migración de {len(books)} libros? (s/n): ", end="")
    response = input().lower().strip()
    
    if response not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Migración cancelada")
        return
    
    # Iniciar migración
    print_separator("MIGRANDO LIBROS")
    
    successful = 0
    failed = 0
    
    for i, book in enumerate(books, 1):
        print(f"\n📚 Procesando {i}/{len(books)}: {book.title}")
        
        if migrate_book_to_cloud_only(book):
            successful += 1
        else:
            failed += 1
    
    # Limpiar directorios locales
    cleanup_local_directories()
    
    # Resumen final
    print_separator("RESUMEN DE MIGRACIÓN")
    print(f"✅ Libros migrados exitosamente: {successful}")
    print(f"❌ Libros con errores: {failed}")
    print(f"📊 Total procesados: {len(books)}")
    
    if successful > 0:
        print("\n🎉 ¡Migración completada!")
        print("La aplicación ahora funciona exclusivamente con Google Drive.")
        print("Los archivos locales han sido eliminados para ahorrar espacio.")

def show_current_status():
    """Muestra el estado actual de la aplicación"""
    print_separator("ESTADO ACTUAL DE LA APLICACIÓN")
    
    db = SessionLocal()
    try:
        total_books = db.query(Book).count()
        books_in_drive = db.query(Book).filter(Book.drive_file_id.isnot(None)).count()
        books_with_local = db.query(Book).filter(Book.file_path.isnot(None)).count()
        
        print(f"📚 Total de libros: {total_books}")
        print(f"☁️ Libros en Google Drive: {books_in_drive}")
        print(f"💾 Libros con archivos locales: {books_with_local}")
        
        if books_in_drive == total_books and books_with_local == 0:
            print("\n✅ La aplicación ya está configurada para almacenamiento exclusivo en la nube")
        else:
            print("\n⚠️ La aplicación aún tiene archivos locales")
            print("   Ejecuta la migración para eliminar archivos locales")
            
    finally:
        db.close()

def main():
    """Función principal"""
    print("🚀 MIGRACIÓN A ALMACENAMIENTO EXCLUSIVO EN LA NUBE")
    print("="*60)
    
    print("\n📋 OPCIONES:")
    print("1. Verificar estado actual")
    print("2. Migrar a almacenamiento exclusivo en la nube")
    print("3. Salir")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    if choice == "1":
        show_current_status()
    elif choice == "2":
        migrate_all_books()
    elif choice == "3":
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main() 