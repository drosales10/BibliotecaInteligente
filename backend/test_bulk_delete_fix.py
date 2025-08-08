#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones de eliminación masiva y carga de etiquetas
"""

import requests
import json
import sys

def test_bulk_delete_and_categories():
    """Prueba las correcciones de eliminación masiva y carga de etiquetas"""
    
    # URL base del backend
    base_url = "http://localhost:8001"
    
    print("🔍 Probando correcciones de eliminación masiva y carga de etiquetas...")
    
    # 1. Probar carga de categorías en modo nube
    print("\n📋 Probando carga de categorías en modo nube...")
    try:
        response = requests.get(f"{base_url}/api/drive/categories/")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Categorías cargadas exitosamente: {len(categories)} categorías encontradas")
            if categories:
                print(f"   Categorías: {', '.join(categories[:5])}{'...' if len(categories) > 5 else ''}")
            else:
                print("   ℹ️ No hay categorías disponibles en modo nube")
        else:
            print(f"❌ Error al cargar categorías: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión al cargar categorías: {e}")
    
    # 2. Probar endpoint de eliminación masiva
    print("\n🗑️ Probando endpoint de eliminación masiva...")
    try:
        # Intentar eliminar con lista vacía (debería dar error 400)
        response = requests.delete(f"{base_url}/api/drive/books/bulk", 
                                 json={"book_ids": []})
        if response.status_code == 400:
            print("✅ Endpoint de eliminación masiva responde correctamente a lista vacía")
        else:
            print(f"⚠️ Endpoint de eliminación masiva no maneja lista vacía como esperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al probar endpoint de eliminación masiva: {e}")
    
    # 3. Probar con IDs inválidos
    print("\n🔍 Probando eliminación masiva con IDs inválidos...")
    try:
        response = requests.delete(f"{base_url}/api/drive/books/bulk", 
                                 json={"book_ids": [99999, 99998]})
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Endpoint de eliminación masiva responde correctamente")
            print(f"   Eliminados: {result.get('deleted_count', 0)}")
            print(f"   Fallidos: {result.get('failed_count', 0)}")
            if result.get('failed_deletions'):
                print(f"   Errores: {result['failed_deletions'][:2]}...")
        else:
            print(f"❌ Error inesperado en eliminación masiva: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al probar eliminación masiva con IDs inválidos: {e}")
    
    # 4. Verificar que el servidor está funcionando
    print("\n🔧 Verificando estado del servidor...")
    try:
        response = requests.get(f"{base_url}/api/test/endpoint")
        if response.status_code == 200:
            print("✅ Servidor backend funcionando correctamente")
        else:
            print(f"⚠️ Servidor backend responde con código: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión al servidor: {e}")
        print("   Asegúrate de que el servidor backend esté ejecutándose en http://localhost:8001")
    
    print("\n🎯 Pruebas completadas")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de correcciones...")
    
    try:
        test_bulk_delete_and_categories()
        print("\n✅ Todas las pruebas completadas")
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
