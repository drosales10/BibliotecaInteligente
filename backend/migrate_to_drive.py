#!/usr/bin/env python3
"""
Script para migrar libros existentes a Google Drive
"""

import os
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

def get_books_not_in_drive():
    """Obtiene libros que no están en Google Drive"""
    print_separator("OBTENIENDO LIBROS PARA MIGRAR")
    
    db = SessionLocal()
    try:
        # Obtener libros que no están en Drive
        books = db.query(Book).filter(Book.is_in_drive == False).all()
        
        print(f"📚 Total de libros encontrados: {len(books)}")
        
        if books:
            print("\n📋 Libros para migrar:")
            for i, book in enumerate(books[:10], 1):
                print(f"  {i}. {book.title} - {book.author}")
                print(f"     Categoría: {book.category}")
                print(f"     Archivo: {os.path.basename(book.file_path)}")
                print()
            
            if len(books) > 10:
                print(f"     ... y {len(books) - 10} libros más")
        
        return books
    finally:
        db.close()

def migrate_book_to_drive(book):
    """Migra un libro individual a Google Drive"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(book.file_path):
            print(f"⚠️ Archivo no encontrado: {book.file_path}")
            return False
        
        # Subir a Google Drive
        drive_info = drive_manager.upload_book_to_drive(
            file_path=book.file_path,
            title=book.title,
            author=book.author,
            category=book.category
        )
        
        if drive_info:
            # Actualizar base de datos
            db = SessionLocal()
            try:
                book.drive_file_id = drive_info['id']
                book.drive_web_link = drive_info['web_view_link']
                book.drive_letter_folder = drive_info['letter_folder']
                book.is_in_drive = True
                db.commit()
                print(f"✅ Migrado: {book.title}")
                return True
            finally:
                db.close()
        else:
            print(f"❌ Error al subir: {book.title}")
            return False
            
    except Exception as e:
        print(f"❌ Error migrando {book.title}: {e}")
        return False

def migrate_all_books():
    """Migra todos los libros a Google Drive"""
    print_separator("INICIANDO MIGRACIÓN A GOOGLE DRIVE")
    
    # Verificar conexión
    if not check_drive_connection():
        return
    
    # Obtener libros para migrar
    books = get_books_not_in_drive()
    
    if not books:
        print("✅ No hay libros para migrar")
        return
    
    # Confirmar migración
    print(f"\n¿Deseas migrar {len(books)} libros a Google Drive? (s/n): ", end="")
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
        
        if migrate_book_to_drive(book):
            successful += 1
        else:
            failed += 1
    
    # Resumen final
    print_separator("RESUMEN DE MIGRACIÓN")
    print(f"✅ Libros migrados exitosamente: {successful}")
    print(f"❌ Libros con errores: {failed}")
    print(f"📊 Total procesados: {len(books)}")
    
    if successful > 0:
        print("\n🎉 ¡Migración completada!")
        print("Los libros ahora están disponibles en Google Drive")
        print("organizados por categorías y orden alfabético.")

def show_drive_info():
    """Muestra información de Google Drive"""
    print_separator("INFORMACIÓN DE GOOGLE DRIVE")
    
    if not check_drive_connection():
        return
    
    try:
        # Obtener información de almacenamiento
        storage_info = drive_manager.get_storage_info()
        print(f"📁 Carpeta raíz: {storage_info['root_folder_name']}")
        print(f"💾 Tamaño total: {storage_info['total_size_gb']} GB")
        print(f"📊 Tamaño en MB: {storage_info['total_size_mb']} MB")
        
        # Contar libros en Drive
        db = SessionLocal()
        try:
            books_in_drive = db.query(Book).filter(Book.is_in_drive == True).count()
            total_books = db.query(Book).count()
            
            print(f"\n📚 Libros en Google Drive: {books_in_drive}/{total_books}")
            print(f"📈 Porcentaje: {(books_in_drive/total_books*100):.1f}%" if total_books > 0 else "📈 Porcentaje: 0%")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")

def main():
    """Función principal"""
    print("🚀 MIGRACIÓN A GOOGLE DRIVE")
    print("="*60)
    
    print("\n📋 OPCIONES:")
    print("1. Verificar conexión con Google Drive")
    print("2. Mostrar información de Google Drive")
    print("3. Migrar todos los libros a Google Drive")
    print("4. Salir")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        check_drive_connection()
    elif choice == "2":
        show_drive_info()
    elif choice == "3":
        migrate_all_books()
    elif choice == "4":
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main() 