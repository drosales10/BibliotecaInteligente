#!/usr/bin/env python3
"""
Test script para verificar las correcciones SSL en la sincronización de libros locales a la nube
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_drive_manager import GoogleDriveManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ssl_sync_fixes():
    """Prueba las correcciones SSL en las funciones de sincronización"""
    
    print("🔍 Iniciando pruebas de correcciones SSL para sincronización...")
    
    try:
        # Inicializar el gestor de Google Drive
        drive_manager = GoogleDriveManager()
        
        if not drive_manager.service:
            print("❌ No se pudo inicializar el servicio de Google Drive")
            return False
        
        print("✅ Servicio de Google Drive inicializado correctamente")
        
        # Probar get_or_create_category_folder
        print("\n📁 Probando get_or_create_category_folder...")
        try:
            category_folder_id = drive_manager.get_or_create_category_folder("Test Category")
            if category_folder_id:
                print(f"✅ Carpeta de categoría creada/encontrada: {category_folder_id}")
            else:
                print("❌ No se pudo crear/encontrar la carpeta de categoría")
                return False
        except Exception as e:
            print(f"❌ Error en get_or_create_category_folder: {e}")
            return False
        
        # Probar get_letter_folder
        print("\n📁 Probando get_letter_folder...")
        try:
            letter_folder_id = drive_manager.get_letter_folder(category_folder_id, "Test Book Title")
            if letter_folder_id:
                print(f"✅ Carpeta de letra creada/encontrada: {letter_folder_id}")
            else:
                print("❌ No se pudo crear/encontrar la carpeta de letra")
                return False
        except Exception as e:
            print(f"❌ Error en get_letter_folder: {e}")
            return False
        
        # Probar upload_book_to_drive (con un archivo de prueba)
        print("\n📤 Probando upload_book_to_drive...")
        try:
            # Crear un archivo de prueba temporal
            test_file_path = "test_book.pdf"
            with open(test_file_path, 'w') as f:
                f.write("Test book content")
            
            result = drive_manager.upload_book_to_drive(test_file_path, "Test Book", "Test Author", "Test Category")
            
            # Limpiar archivo de prueba
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            
            if result and result.get('success'):
                print(f"✅ Libro subido exitosamente: {result.get('file_id')}")
                
                # Probar delete_book_from_drive
                print("\n🗑️ Probando delete_book_from_drive...")
                try:
                    delete_result = drive_manager.delete_book_from_drive(result.get('file_id'))
                    if delete_result and delete_result.get('success'):
                        print("✅ Libro eliminado exitosamente")
                    else:
                        print(f"❌ Error al eliminar libro: {delete_result.get('error')}")
                        return False
                except Exception as e:
                    print(f"❌ Error en delete_book_from_drive: {e}")
                    return False
            else:
                print(f"❌ Error al subir libro: {result.get('error') if result else 'Unknown error'}")
                return False
        except Exception as e:
            print(f"❌ Error en upload_book_to_drive: {e}")
            return False
        
        print("\n🎉 ¡Todas las pruebas SSL pasaron exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error general en las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = test_ssl_sync_fixes()
    if success:
        print("\n✅ Todas las correcciones SSL están funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Algunas correcciones SSL fallaron")
        sys.exit(1)
