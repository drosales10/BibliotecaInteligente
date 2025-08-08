#!/usr/bin/env python3
"""
Script de prueba simple para la funcionalidad de carga de carpeta en modo nube
"""

import sys
import os
import json
import requests
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_endpoints():
    """Prueba endpoints básicos"""
    print("🔍 Probando endpoints básicos...")
    
    # Probar endpoint de estado
    try:
        response = requests.get('http://localhost:8001/api/drive/status', timeout=10)
        print(f"✅ Estado de Drive: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Configurado: {data.get('configured', False)}")
    except Exception as e:
        print(f"❌ Error en estado: {e}")
    
    # Probar endpoint de salud
    try:
        response = requests.get('http://localhost:8001/api/drive/health', timeout=10)
        print(f"✅ Salud de Drive: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en salud: {e}")

def test_google_drive_manager():
    """Prueba el GoogleDriveManager directamente"""
    print("\n🔍 Probando GoogleDriveManager...")
    
    try:
        from google_drive_manager import get_drive_manager
        
        drive_manager = get_drive_manager()
        print("✅ GoogleDriveManager inicializado")
        
        if not drive_manager.service:
            print("❌ Servicio no disponible")
            return False
        
        print("✅ Servicio de Google Drive disponible")
        
        # Probar extracción de ID de URL
        test_urls = [
            "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "https://drive.google.com/drive/u/0/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        ]
        
        for url in test_urls:
            folder_id = drive_manager.extract_folder_id_from_url(url)
            print(f"   URL: {url[:50]}...")
            print(f"   ID extraído: {folder_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_folder_upload_with_mock():
    """Prueba la carga de carpeta con datos simulados"""
    print("\n🔍 Probando carga de carpeta con datos simulados...")
    
    # Simular una carpeta con algunos archivos
    mock_folder_data = {
        "folder_url": "https://drive.google.com/drive/folders/test_folder_id"
    }
    
    try:
        response = requests.post(
            'http://localhost:8001/api/upload-drive-folder/',
            json=mock_folder_data,
            timeout=10
        )
        
        print(f"📊 Respuesta: {response.status_code}")
        if response.status_code != 200:
            error_text = response.text
            print(f"   Error: {error_text}")
            
            # Verificar si es el error esperado de accesibilidad
            if "Error de accesibilidad" in error_text:
                print("✅ Error esperado: La carpeta no es accesible (es normal para URLs de prueba)")
                return True
            else:
                print("❌ Error inesperado")
                return False
        else:
            print("✅ Respuesta exitosa")
            return True
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_local_folder_upload():
    """Prueba la carga de carpeta local (que debería funcionar)"""
    print("\n🔍 Probando carga de carpeta local...")
    
    # Crear una carpeta temporal con algunos archivos de prueba
    temp_folder = "test_upload_folder"
    os.makedirs(temp_folder, exist_ok=True)
    
    # Crear algunos archivos de prueba
    test_files = [
        "test1.pdf",
        "test2.epub",
        "test3.txt"  # Este debería ser ignorado
    ]
    
    for filename in test_files:
        filepath = os.path.join(temp_folder, filename)
        with open(filepath, 'w') as f:
            f.write(f"Contenido de prueba para {filename}")
    
    try:
        # Probar el endpoint de carpeta local
        response = requests.post(
            'http://localhost:8001/upload-folder/',
            params={'folder_path': os.path.abspath(temp_folder)},
            timeout=30
        )
        
        print(f"📊 Respuesta carpeta local: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total archivos: {data.get('total_files', 0)}")
            print(f"   Exitosos: {data.get('successful', 0)}")
            print(f"   Fallidos: {data.get('failed', 0)}")
            print(f"   Duplicados: {data.get('duplicates', 0)}")
            return True
        else:
            error_text = response.text
            print(f"   Error: {error_text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba local: {e}")
        return False
    finally:
        # Limpiar carpeta temporal
        try:
            import shutil
            shutil.rmtree(temp_folder)
        except:
            pass

def main():
    """Función principal"""
    print("🧪 PRUEBAS SIMPLES DE CARGA DE CARPETA")
    print("=" * 50)
    
    # Verificar servidor
    try:
        response = requests.get('http://localhost:8001/', timeout=5)
        print("✅ Servidor ejecutándose")
    except:
        print("❌ Servidor no disponible")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Endpoints básicos", test_basic_endpoints),
        ("GoogleDriveManager", test_google_drive_manager),
        ("Carga de carpeta (mock)", test_folder_upload_with_mock),
        ("Carga de carpeta local", test_local_folder_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print(f"\n{'='*50}")
    print("📊 RESUMEN")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")

if __name__ == "__main__":
    main()
