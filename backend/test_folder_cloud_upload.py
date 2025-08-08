#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de carga de carpeta local en modo nube
"""

import sys
import os
import json
import requests
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_folder_cloud_upload():
    """Prueba la carga de carpeta local en modo nube"""
    print("🔍 Probando carga de carpeta local en modo nube...")
    
    # Crear una carpeta temporal con archivos de prueba
    temp_folder = "test_cloud_folder"
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
        # Crear FormData con los archivos
        files = []
        for filename in test_files:
            if filename.lower().endswith(('.pdf', '.epub')):
                filepath = os.path.join(temp_folder, filename)
                with open(filepath, 'rb') as f:
                    files.append(('files', (filename, f.read(), 'application/octet-stream')))
        
        data = {
            'folder_name': temp_folder,
            'total_files': len([f for f in test_files if f.lower().endswith(('.pdf', '.epub'))])
        }
        
        print(f"📁 Enviando {len(files)} archivos desde carpeta: {temp_folder}")
        
        response = requests.post(
            'http://localhost:8001/api/upload-folder-cloud/',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Respuesta del servidor: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Carga de carpeta exitosa!")
            print(f"   📚 Total de archivos: {result.get('total_files', 0)}")
            print(f"   ✅ Exitosos: {result.get('successful', 0)}")
            print(f"   ❌ Fallidos: {result.get('failed', 0)}")
            print(f"   ⚠️ Duplicados: {result.get('duplicates', 0)}")
            print(f"   📝 Mensaje: {result.get('message', 'N/A')}")
            return True
        else:
            error_text = response.text
            print(f"❌ Error en carga de carpeta: {response.status_code}")
            print(f"   Detalles: {error_text}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
    finally:
        # Limpiar carpeta temporal
        try:
            import shutil
            shutil.rmtree(temp_folder)
        except:
            pass

def test_endpoint_exists():
    """Verifica que el endpoint existe"""
    print("🔍 Verificando que el endpoint existe...")
    
    try:
        response = requests.get('http://localhost:8001/docs', timeout=5)
        if response.status_code == 200:
            print("✅ Documentación de API disponible")
            return True
        else:
            print("❌ No se pudo acceder a la documentación")
            return False
    except Exception as e:
        print(f"❌ Error conectando con el servidor: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 PRUEBA DE CARGA DE CARPETA LOCAL EN MODO NUBE")
    print("=" * 60)
    
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
        ("Verificación de endpoint", test_endpoint_exists),
        ("Carga de carpeta local en modo nube", test_folder_cloud_upload)
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
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
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
