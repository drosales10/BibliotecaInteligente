#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de eliminación de libros
"""

import requests
import json
import sys

def test_delete_endpoint():
    """Prueba el endpoint de eliminación de libros"""
    
    # URL base del backend
    base_url = "http://localhost:8001"
    
    print("🔍 Probando endpoint de eliminación de libros...")
    
    # 1. Primero, obtener la lista de libros para ver qué libros están disponibles
    print("\n📋 Obteniendo lista de libros...")
    try:
        response = requests.get(f"{base_url}/api/books/")
        if response.status_code == 200:
            books = response.json()
            print(f"✅ Encontrados {len(books)} libros")
            
            if len(books) == 0:
                print("❌ No hay libros disponibles para probar eliminación")
                return False
            
            # Mostrar los primeros 3 libros
            for i, book in enumerate(books[:3]):
                print(f"  {i+1}. ID: {book.get('id')}, Título: {book.get('title')}")
            
            # Usar el primer libro para la prueba
            test_book = books[0]
            book_id = test_book.get('id')
            book_title = test_book.get('title')
            
        else:
            print(f"❌ Error al obtener libros: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    # 2. Probar eliminación en modo local
    print(f"\n🗑️ Probando eliminación en modo local para libro: {book_title} (ID: {book_id})")
    try:
        response = requests.delete(f"{base_url}/api/books/{book_id}")
        print(f"📊 Respuesta: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print("✅ Eliminación en modo local exitosa")
        else:
            print("❌ Error en eliminación en modo local")
            
    except Exception as e:
        print(f"❌ Error al eliminar en modo local: {e}")
    
    # 3. Probar eliminación en modo nube (si hay libros en Drive)
    print(f"\n☁️ Probando eliminación en modo nube...")
    try:
        response = requests.get(f"{base_url}/api/drive/books/")
        if response.status_code == 200:
            drive_books = response.json()
            print(f"✅ Encontrados {len(drive_books)} libros en Google Drive")
            
            if len(drive_books) > 0:
                test_drive_book = drive_books[0]
                drive_book_id = test_drive_book.get('id')
                drive_book_title = test_drive_book.get('title')
                
                print(f"🗑️ Probando eliminación en Drive para: {drive_book_title} (ID: {drive_book_id})")
                
                response = requests.delete(f"{base_url}/api/drive/books/{drive_book_id}")
                print(f"📊 Respuesta: {response.status_code} - {response.text}")
                
                if response.status_code == 200:
                    print("✅ Eliminación en modo nube exitosa")
                else:
                    print("❌ Error en eliminación en modo nube")
            else:
                print("ℹ️ No hay libros en Google Drive para probar")
        else:
            print(f"❌ Error al obtener libros de Drive: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al eliminar en modo nube: {e}")
    
    print("\n🎯 Prueba completada")
    return True

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de endpoint de eliminación...")
    
    try:
        success = test_delete_endpoint()
        if success:
            print("✅ Pruebas completadas exitosamente")
            return 0
        else:
            print("❌ Algunas pruebas fallaron")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
