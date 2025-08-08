#!/usr/bin/env python3
"""
Script de depuración para verificar el estado de las portadas
Compara las portadas registradas en la base de datos con los archivos físicos
"""

import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def check_covers_status():
    """Verifica el estado de las portadas en la base de datos vs archivos físicos"""
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Obtener todos los libros
        books = db.query(models.Book).all()
        
        print("🔍 VERIFICACIÓN DE PORTADAS")
        print("=" * 50)
        
        # Contadores
        total_books = len(books)
        books_with_covers = 0
        covers_in_db = 0
        covers_in_filesystem = 0
        missing_covers = 0
        orphaned_files = 0
        
        # Obtener archivos físicos de portadas
        covers_dir = "static/covers"
        physical_covers = set()
        if os.path.exists(covers_dir):
            for filename in os.listdir(covers_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    physical_covers.add(filename)
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Total de libros en BD: {total_books}")
        print(f"   • Archivos de portada físicos: {len(physical_covers)}")
        print()
        
        print("📚 LIBROS CON PORTADAS:")
        print("-" * 30)
        
        for book in books:
            has_cover = False
            cover_status = "❌ Sin portada"
            
            if book.cover_image_url:
                covers_in_db += 1
                
                # Extraer nombre del archivo de la URL
                cover_filename = None
                if book.cover_image_url.startswith('/static/covers/'):
                    cover_filename = book.cover_image_url.replace('/static/covers/', '')
                elif book.cover_image_url.startswith('http://localhost:8001/static/covers/'):
                    cover_filename = book.cover_image_url.replace('http://localhost:8001/static/covers/', '')
                elif '/' not in book.cover_image_url and '.' in book.cover_image_url:
                    # Es solo el nombre del archivo
                    cover_filename = book.cover_image_url
                
                if cover_filename:
                    if cover_filename in physical_covers:
                        has_cover = True
                        covers_in_filesystem += 1
                        cover_status = "✅ Portada existe"
                        books_with_covers += 1
                    else:
                        cover_status = "❌ Archivo faltante"
                        missing_covers += 1
                else:
                    cover_status = "⚠️ URL malformada"
            
            print(f"   • ID {book.id}: {book.title[:30]}... - {cover_status}")
            if book.cover_image_url:
                print(f"     URL: {book.cover_image_url}")
        
        print()
        print("📁 ARCHIVOS FÍSICOS DE PORTADAS:")
        print("-" * 30)
        
        # Verificar archivos físicos
        for cover_file in sorted(physical_covers):
            # Buscar si algún libro usa esta portada
            used_by_books = []
            for book in books:
                if book.cover_image_url and cover_file in book.cover_image_url:
                    used_by_books.append(book.id)
            
            if used_by_books:
                print(f"   ✅ {cover_file} - Usado por libros: {used_by_books}")
            else:
                print(f"   🗑️ {cover_file} - ORFANO (no usado por ningún libro)")
                orphaned_files += 1
        
        print()
        print("📊 RESUMEN:")
        print("=" * 30)
        print(f"   • Libros con portadas: {books_with_covers}/{total_books}")
        print(f"   • Portadas en BD: {covers_in_db}")
        print(f"   • Portadas en sistema de archivos: {covers_in_filesystem}")
        print(f"   • Portadas faltantes: {missing_covers}")
        print(f"   • Archivos huérfanos: {orphaned_files}")
        
        if missing_covers > 0:
            print()
            print("⚠️ PROBLEMAS DETECTADOS:")
            print("-" * 20)
            print(f"   • {missing_covers} libros tienen URL de portada pero el archivo no existe")
        
        if orphaned_files > 0:
            print()
            print("🗑️ ARCHIVOS HUÉRFANOS:")
            print("-" * 20)
            print(f"   • {orphaned_files} archivos de portada no están asociados a ningún libro")
            print("   • Puedes usar el botón 'Limpiar Portadas' para eliminarlos")
        
        return {
            'total_books': total_books,
            'books_with_covers': books_with_covers,
            'covers_in_db': covers_in_db,
            'covers_in_filesystem': covers_in_filesystem,
            'missing_covers': missing_covers,
            'orphaned_files': orphaned_files
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    check_covers_status()
