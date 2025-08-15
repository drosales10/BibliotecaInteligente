#!/usr/bin/env python3
"""
Script de migración para corregir las rutas de archivos en la base de datos.
Elimina las carpetas de las rutas y deja solo los nombres de archivo.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Book
from sqlalchemy import text

def migrate_file_paths():
    """
    Migra las rutas de archivos existentes para eliminar las carpetas
    y dejar solo los nombres de archivo.
    """
    db = SessionLocal()
    
    try:
        print("🔍 Iniciando migración de rutas de archivos...")
        
        # Obtener todos los libros que tengan file_path
        books_with_path = db.query(Book).filter(Book.file_path.isnot(None)).all()
        
        if not books_with_path:
            print("✅ No hay libros con rutas de archivo para migrar.")
            return
        
        print(f"📚 Encontrados {len(books_with_path)} libros con rutas de archivo.")
        
        migrated_count = 0
        skipped_count = 0
        
        for book in books_with_path:
            if not book.file_path:
                continue
                
            # Verificar si la ruta contiene carpetas (tiene separadores de directorio)
            if '/' in book.file_path or '\\' in book.file_path:
                # Extraer solo el nombre del archivo
                old_path = book.file_path
                new_path = os.path.basename(book.file_path)
                
                print(f"🔄 Migrando: '{old_path}' -> '{new_path}'")
                
                # Actualizar en la base de datos
                book.file_path = new_path
                migrated_count += 1
            else:
                # Ya es solo el nombre del archivo
                skipped_count += 1
        
        # Confirmar cambios
        db.commit()
        
        print(f"✅ Migración completada:")
        print(f"   • Libros migrados: {migrated_count}")
        print(f"   • Libros sin cambios: {skipped_count}")
        print(f"   • Total procesados: {len(books_with_path)}")
        
        # Verificar que la migración fue exitosa
        print("\n🔍 Verificando migración...")
        books_after = db.query(Book).filter(Book.file_path.isnot(None)).all()
        
        for book in books_after:
            if book.file_path and ('/' in book.file_path or '\\' in book.file_path):
                print(f"⚠️  ADVERTENCIA: Libro {book.id} aún tiene ruta completa: {book.file_path}")
            else:
                print(f"✅ Libro {book.id}: {book.file_path}")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_migration():
    """
    Verifica que la migración fue exitosa.
    """
    db = SessionLocal()
    
    try:
        print("\n🔍 Verificando estado de la migración...")
        
        # Contar libros con rutas completas
        books_with_full_path = db.query(Book).filter(
            text("file_path LIKE '%/%' OR file_path LIKE '%\\%'")
        ).all()
        
        if books_with_full_path:
            print(f"❌ ADVERTENCIA: {len(books_with_full_path)} libros aún tienen rutas completas:")
            for book in books_with_full_path:
                print(f"   • ID {book.id}: {book.title} - {book.file_path}")
        else:
            print("✅ Todos los libros tienen solo nombres de archivo.")
        
        # Mostrar algunos ejemplos
        sample_books = db.query(Book).filter(Book.file_path.isnot(None)).limit(5).all()
        if sample_books:
            print(f"\n📋 Ejemplos de rutas después de la migración:")
            for book in sample_books:
                print(f"   • {book.title}: {book.file_path}")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Script de migración de rutas de archivos")
    print("=" * 50)
    
    try:
        migrate_file_paths()
        verify_migration()
        print("\n✅ Migración completada exitosamente.")
    except Exception as e:
        print(f"\n❌ La migración falló: {e}")
        sys.exit(1)
