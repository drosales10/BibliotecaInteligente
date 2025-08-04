#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de borrado de libros
"""

import requests
import json
import os
from database import SessionLocal
from models import Book

# Configuración
BASE_URL = "http://localhost:8000"

def print_separator(title):
    """Imprime un separador con título"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def test_get_books():
    """Obtiene la lista actual de libros"""
    print_separator("OBTENIENDO LISTA ACTUAL DE LIBROS")
    
    try:
        response = requests.get(f"{BASE_URL}/books/")
        if response.status_code == 200:
            books = response.json()
            print(f"✅ Total de libros en la base de datos: {len(books)}")
            
            if books:
                print("\n📚 Primeros 5 libros:")
                for i, book in enumerate(books[:5], 1):
                    print(f"  {i}. ID: {book['id']}, Título: {book['title']}")
                    print(f"     Archivo: {book['file_path']}")
                    print(f"     Existe archivo: {os.path.exists(book['file_path']) if book['file_path'] else 'N/A'}")
                    print()
            return books
        else:
            print(f"❌ Error al obtener libros: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return []

def test_delete_single_book(book_id):
    """Prueba el borrado de un libro individual"""
    print_separator(f"PRUEBA DE BORRADO INDIVIDUAL - ID: {book_id}")
    
    try:
        # Verificar que el libro existe antes del borrado
        response = requests.get(f"{BASE_URL}/books/")
        if response.status_code == 200:
            books = response.json()
            book_exists = any(book['id'] == book_id for book in books)
            if not book_exists:
                print(f"❌ El libro con ID {book_id} no existe")
                return False
        
        # Realizar el borrado
        response = requests.delete(f"{BASE_URL}/books/{book_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Borrado exitoso: {result['message']}")
            return True
        else:
            print(f"❌ Error en borrado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el borrado: {e}")
        return False

def test_delete_multiple_books(book_ids):
    """Prueba el borrado múltiple de libros"""
    print_separator(f"PRUEBA DE BORRADO MÚLTIPLE - IDs: {book_ids}")
    
    try:
        payload = {"book_ids": book_ids}
        response = requests.delete(f"{BASE_URL}/books/bulk", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Borrado múltiple exitoso:")
            print(f"   Libros eliminados: {result['deleted_count']}")
            print(f"   Títulos: {result['deleted_books']}")
            if result['failed_deletions']:
                print(f"   Errores: {result['failed_deletions']}")
            return True
        else:
            print(f"❌ Error en borrado múltiple: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el borrado múltiple: {e}")
        return False

def test_delete_by_category(category):
    """Prueba el borrado por categoría"""
    print_separator(f"PRUEBA DE BORRADO POR CATEGORÍA - {category}")
    
    try:
        response = requests.delete(f"{BASE_URL}/categories/{category}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Borrado por categoría exitoso: {result['message']}")
            return True
        else:
            print(f"❌ Error en borrado por categoría: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el borrado por categoría: {e}")
        return False

def verify_file_cleanup():
    """Verifica que los archivos físicos se hayan eliminado correctamente"""
    print_separator("VERIFICACIÓN DE LIMPIEZA DE ARCHIVOS")
    
    try:
        # Verificar archivos en la carpeta books
        books_dir = "books"
        if os.path.exists(books_dir):
            files = os.listdir(books_dir)
            print(f"📁 Archivos restantes en {books_dir}: {len(files)}")
            
            if files:
                print("   Archivos encontrados:")
                for file in files[:10]:  # Mostrar solo los primeros 10
                    file_path = os.path.join(books_dir, file)
                    size = os.path.getsize(file_path) if os.path.isfile(file_path) else "DIR"
                    print(f"     - {file} ({size} bytes)")
                if len(files) > 10:
                    print(f"     ... y {len(files) - 10} archivos más")
            else:
                print("   ✅ No hay archivos restantes")
        else:
            print("   📁 La carpeta books no existe")
        
        # Verificar archivos de portada
        covers_dir = "static/covers"
        if os.path.exists(covers_dir):
            cover_files = os.listdir(covers_dir)
            print(f"🖼️  Archivos de portada restantes: {len(cover_files)}")
            
            if cover_files:
                print("   Portadas encontradas:")
                for file in cover_files[:5]:
                    print(f"     - {file}")
                if len(cover_files) > 5:
                    print(f"     ... y {len(cover_files) - 5} archivos más")
            else:
                print("   ✅ No hay archivos de portada restantes")
        else:
            print("   🖼️  La carpeta de portadas no existe")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE BORRADO")
    print("="*60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/books/")
        if response.status_code != 200:
            print("❌ El servidor no está corriendo. Inicia el backend primero.")
            return
    except:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté corriendo en http://localhost:8000")
        return
    
    # Obtener lista inicial de libros
    initial_books = test_get_books()
    
    if not initial_books:
        print("❌ No hay libros para probar el borrado")
        return
    
    # Mostrar opciones de prueba
    print("\n📋 OPCIONES DE PRUEBA:")
    print("1. Borrado individual de un libro")
    print("2. Borrado múltiple de libros")
    print("3. Borrado por categoría")
    print("4. Verificar limpieza de archivos")
    print("5. Ejecutar todas las pruebas")
    
    choice = input("\nSelecciona una opción (1-5): ").strip()
    
    if choice == "1":
        book_id = int(input("Ingresa el ID del libro a eliminar: "))
        test_delete_single_book(book_id)
        
    elif choice == "2":
        ids_input = input("Ingresa los IDs separados por coma (ej: 1,2,3): ")
        book_ids = [int(id.strip()) for id in ids_input.split(",")]
        test_delete_multiple_books(book_ids)
        
    elif choice == "3":
        category = input("Ingresa el nombre de la categoría a eliminar: ")
        test_delete_by_category(category)
        
    elif choice == "4":
        verify_file_cleanup()
        
    elif choice == "5":
        # Ejecutar todas las pruebas
        if len(initial_books) >= 2:
            # Borrado individual
            test_delete_single_book(initial_books[0]['id'])
            
            # Borrado múltiple (si hay suficientes libros)
            if len(initial_books) >= 3:
                test_delete_multiple_books([initial_books[1]['id'], initial_books[2]['id']])
            
            # Verificar limpieza
            verify_file_cleanup()
        else:
            print("❌ No hay suficientes libros para ejecutar todas las pruebas")
    
    # Verificar estado final
    print_separator("ESTADO FINAL")
    final_books = test_get_books()
    print(f"📊 Libros restantes: {len(final_books)}")
    verify_file_cleanup()
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    main() 