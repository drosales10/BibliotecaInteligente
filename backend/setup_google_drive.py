#!/usr/bin/env python3
"""
Script de configuración para Google Drive
Guía al usuario en el proceso de configuración de la API de Google Drive
"""

import os
import json
from google_drive_manager import GoogleDriveManager

def print_banner():
    """Imprime el banner de bienvenida"""
    print("=" * 60)
    print("🚀 CONFIGURACIÓN DE GOOGLE DRIVE PARA BIBLIOTECA INTELIGENTE")
    print("=" * 60)
    print()

def print_instructions():
    """Imprime las instrucciones de configuración"""
    print("📋 INSTRUCCIONES DE CONFIGURACIÓN:")
    print()
    print("1. Ve a Google Cloud Console: https://console.cloud.google.com/")
    print("2. Crea un nuevo proyecto o selecciona uno existente")
    print("3. Habilita la API de Google Drive")
    print("4. Crea credenciales de OAuth 2.0")
    print("5. Descarga el archivo credentials.json")
    print("6. Coloca el archivo en la carpeta backend/")
    print()
    print("🔗 ENLACES ÚTILES:")
    print("• Google Cloud Console: https://console.cloud.google.com/")
    print("• Google Drive API: https://developers.google.com/drive/api")
    print("• OAuth 2.0 Setup: https://developers.google.com/identity/protocols/oauth2")
    print()

def check_credentials():
    """Verifica si existe el archivo de credenciales"""
    if os.path.exists('credentials.json'):
        print("✅ Archivo credentials.json encontrado")
        return True
    else:
        print("❌ Archivo credentials.json no encontrado")
        print("   Por favor, descarga el archivo desde Google Cloud Console")
        return False

def test_connection():
    """Prueba la conexión con Google Drive"""
    print("\n🔗 Probando conexión con Google Drive...")
    
    try:
        drive_manager = GoogleDriveManager()
        
        if drive_manager.service:
            print("✅ Conexión exitosa con Google Drive")
            
            # Obtener información de almacenamiento
            storage_info = drive_manager.get_storage_info()
            if storage_info:
                print(f"📁 Carpeta raíz: {storage_info['root_folder_name']}")
                print(f"💾 Tamaño total: {storage_info['total_size_mb']} MB")
            
            return True
        else:
            print("❌ Error al conectar con Google Drive")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba de conexión: {e}")
        return False

def create_sample_structure():
    """Crea una estructura de ejemplo en Google Drive"""
    print("\n📁 Creando estructura de ejemplo...")
    
    try:
        drive_manager = GoogleDriveManager()
        
        # Crear algunas categorías de ejemplo
        sample_categories = ["Psicología", "Filosofía", "Ciencia"]
        
        for category in sample_categories:
            folder_id = drive_manager.get_or_create_category_folder(category)
            if folder_id:
                print(f"✅ Categoría creada: {category}")
            
            # Crear carpetas de letras de ejemplo
            for letter in ['A', 'B', 'C']:
                letter_folder_id = drive_manager.get_letter_folder(folder_id, f"{letter} - Ejemplo")
                if letter_folder_id:
                    print(f"   📂 Carpeta de letra creada: {letter}")
        
        print("✅ Estructura de ejemplo creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear estructura de ejemplo: {e}")
        return False

def main():
    """Función principal"""
    print_banner()
    
    # Verificar credenciales
    if not check_credentials():
        print_instructions()
        return
    
    # Probar conexión
    if not test_connection():
        print("\n❌ No se pudo establecer conexión con Google Drive")
        print("   Verifica que el archivo credentials.json sea correcto")
        return
    
    # Crear estructura de ejemplo
    print("\n¿Deseas crear una estructura de ejemplo en Google Drive? (s/n): ", end="")
    response = input().lower().strip()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        create_sample_structure()
    
    print("\n🎉 Configuración completada exitosamente!")
    print("La biblioteca ahora puede almacenar libros en Google Drive")
    print("organizados por categorías y orden alfabético A-Z")

if __name__ == "__main__":
    main() 