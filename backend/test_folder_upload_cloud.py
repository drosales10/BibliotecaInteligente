#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de carga de carpeta en modo nube
"""

import sys
import os
import json
import requests
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_drive_status():
    """Prueba el estado de Google Drive"""
    print("🔍 Probando estado de Google Drive...")
    
    try:
        response = requests.get('http://localhost:8001/api/drive/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Google Drive está configurado: {data.get('configured', False)}")
            if data.get('configured'):
                print(f"   📁 Carpeta raíz: {data.get('root_folder_name', 'N/A')}")
                print(f"   📊 Espacio usado: {data.get('storage_used', 'N/A')}")
            return True
        else:
            print(f"❌ Error en estado de Google Drive: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando con el servidor: {e}")
        return False

def test_folder_upload_endpoint():
    """Prueba el endpoint de carga de carpeta"""
    print("\n🔍 Probando endpoint de carga de carpeta...")
    
    # URL de ejemplo de una carpeta pública de Google Drive
    test_folder_url = "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    
    payload = {
        "folder_url": test_folder_url
    }
    
    try:
        print(f"📁 Enviando solicitud para carpeta: {test_folder_url}")
        response = requests.post(
            'http://localhost:8001/api/upload-drive-folder/',
            json=payload,
            timeout=30
        )
        
        print(f"📊 Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Carga de carpeta exitosa!")
            print(f"   📚 Total de archivos: {data.get('total_files', 0)}")
            print(f"   ✅ Exitosos: {data.get('successful', 0)}")
            print(f"   ❌ Fallidos: {data.get('failed', 0)}")
            print(f"   ⚠️ Duplicados: {data.get('duplicates', 0)}")
            print(f"   📝 Mensaje: {data.get('message', 'N/A')}")
            return True
        else:
            error_text = response.text
            print(f"❌ Error en carga de carpeta: {response.status_code}")
            print(f"   Detalles: {error_text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La operación tardó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def test_google_drive_manager_methods():
    """Prueba los métodos del GoogleDriveManager"""
    print("\n🔍 Probando métodos del GoogleDriveManager...")
    
    try:
        from google_drive_manager import get_drive_manager
        
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            print("❌ Google Drive no está configurado")
            return False
        
        print("✅ Google Drive Manager inicializado correctamente")
        
        # Probar método de verificación de accesibilidad
        test_url = "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        print(f"🔍 Probando accesibilidad de carpeta: {test_url}")
        
        accessibility = drive_manager.check_folder_accessibility(test_url)
        if accessibility.get("success"):
            print("✅ Carpeta es accesible")
            print(f"   📁 Nombre: {accessibility.get('folder_info', {}).get('name', 'N/A')}")
            print(f"   👤 Propietario: {accessibility.get('owner', 'N/A')}")
        else:
            print(f"❌ Carpeta no accesible: {accessibility.get('error', 'Error desconocido')}")
            return False
        
        # Probar listado de contenido
        print("🔍 Probando listado de contenido de carpeta...")
        folder_contents = drive_manager.list_public_folder_contents(test_url)
        if folder_contents.get("success"):
            print("✅ Contenido de carpeta listado correctamente")
            files = folder_contents.get("files", [])
            print(f"   📄 Archivos encontrados: {len(files)}")
            for file in files[:5]:  # Mostrar solo los primeros 5
                print(f"      - {file.get('name', 'N/A')}")
            if len(files) > 5:
                print(f"      ... y {len(files) - 5} más")
        else:
            print(f"❌ Error listando contenido: {folder_contents.get('error', 'Error desconocido')}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando GoogleDriveManager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error probando métodos: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🧪 PRUEBAS DE CARGA DE CARPETA EN MODO NUBE")
    print("=" * 50)
    
    # Verificar que el servidor esté ejecutándose
    print("🔍 Verificando que el servidor esté ejecutándose...")
    try:
        response = requests.get('http://localhost:8001/', timeout=5)
        print("✅ Servidor está ejecutándose")
    except:
        print("❌ El servidor no está ejecutándose en http://localhost:8001")
        print("   Ejecuta: python main.py")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Estado de Google Drive", test_drive_status),
        ("Métodos de GoogleDriveManager", test_google_drive_manager_methods),
        ("Endpoint de carga de carpeta", test_folder_upload_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La funcionalidad está funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
