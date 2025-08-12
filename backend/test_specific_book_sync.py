#!/usr/bin/env python3
"""
Script para probar la sincronización de un libro específico
"""

import os
import sys
import traceback
from pathlib import Path

def test_book_sync(book_id=506):
    """Prueba la sincronización de un libro específico"""
    print(f"🧪 PROBANDO SINCRONIZACIÓN DEL LIBRO {book_id}")
    print("=" * 60)
    
    try:
        # Importar módulos necesarios
        import database
        import crud
        from google_drive_manager import get_drive_manager
        from sqlalchemy import text
        
        print("✅ Módulos importados correctamente")
        
        # Conectar a la base de datos
        db = database.SessionLocal()
        print("✅ Conexión a base de datos establecida")
        
        # Obtener información del libro
        print(f"🔍 Buscando libro con ID: {book_id}")
        book = crud.get_book(db, book_id)
        
        if not book:
            print(f"❌ Libro con ID {book_id} no encontrado en la base de datos")
            return False
        
        print(f"📚 Libro encontrado: {book.title} - {book.author}")
        print(f"📁 Ruta del archivo: {book.file_path}")
        print(f"📊 Estado actual: synced_to_drive={book.synced_to_drive}, drive_file_id={book.drive_file_id}")
        
        # Verificar si el archivo existe
        if not book.file_path:
            print("❌ El libro no tiene ruta de archivo configurada")
            return False
            
        if not os.path.exists(book.file_path):
            print(f"❌ El archivo no existe en la ruta: {book.file_path}")
            return False
            
        print(f"✅ Archivo encontrado en: {book.file_path}")
        print(f"📏 Tamaño del archivo: {os.path.getsize(book.file_path)} bytes")
        
        # Verificar Google Drive Manager
        print("\n🔍 Verificando Google Drive Manager...")
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            print("❌ Google Drive no está configurado")
            return False
            
        print("✅ Google Drive Manager configurado")
        
        # Verificar salud de Drive
        health_result = drive_manager.health_check()
        if health_result['status'] != 'healthy':
            print(f"❌ Google Drive no está saludable: {health_result['message']}")
            return False
            
        print("✅ Google Drive está funcionando correctamente")
        
        # Intentar sincronización
        print(f"\n🔄 Intentando sincronizar libro: {book.title}")
        
        result = drive_manager.upload_book_to_drive(
            book.file_path,
            book.title,
            book.author,
            book.category or "Sin categoría"
        )
        
        print(f"📊 Resultado de la sincronización: {result}")
        
        if result['success']:
            print("✅ Sincronización exitosa!")
            print(f"   📁 Drive File ID: {result['file_id']}")
            print(f"   🌐 Web View Link: {result['drive_info']['web_view_link']}")
            
            # Actualizar estado en la base de datos
            print("🔄 Actualizando estado en la base de datos...")
            crud.update_book_sync_status(
                db,
                book_id=book_id,
                synced_to_drive=True,
                drive_file_id=result['file_id'],
                remove_local_file=False  # No eliminar por ahora
            )
            print("✅ Estado actualizado en la base de datos")
            
            return True
        else:
            print(f"❌ Error en la sincronización: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Función principal"""
    print("🚀 PRUEBA DE SINCRONIZACIÓN DE LIBRO ESPECÍFICO")
    print("=" * 60)
    
    # Probar con el libro 506 (el que está fallando)
    success = test_book_sync(506)
    
    if success:
        print("\n✅ SINCRONIZACIÓN EXITOSA")
        print("El libro se sincronizó correctamente con Google Drive")
    else:
        print("\n❌ SINCRONIZACIÓN FALLÓ")
        print("Revisa los errores anteriores para identificar la causa")

if __name__ == "__main__":
    main()
