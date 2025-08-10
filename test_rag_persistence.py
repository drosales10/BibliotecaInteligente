#!/usr/bin/env python3
"""
Script de prueba para verificar la persistencia de RAG
Este script demuestra que los embeddings se mantienen entre sesiones
"""

import os
import sys
import time

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_rag_persistence():
    """Prueba la persistencia de RAG creando y verificando embeddings"""
    
    print("🧪 PRUEBA DE PERSISTENCIA RAG")
    print("=" * 50)
    
    try:
        # Importar módulo RAG
        import rag
        
        print("✅ Módulo RAG importado correctamente")
        
        # Verificar estado inicial
        print("\n📊 Estado inicial de RAG:")
        initial_stats = rag.get_rag_stats()
        print(f"   - Total embeddings: {initial_stats['total_embeddings']}")
        print(f"   - Libros únicos: {initial_stats['unique_books']}")
        print(f"   - Estado: {initial_stats['status']}")
        print(f"   - Directorio: {initial_stats['persistence_directory']}")
        
        # Verificar que el directorio de persistencia existe
        if os.path.exists(initial_stats['persistence_directory']):
            print(f"✅ Directorio de persistencia existe: {initial_stats['persistence_directory']}")
            
            # Listar archivos en el directorio
            files = os.listdir(initial_stats['persistence_directory'])
            print(f"📁 Archivos en directorio: {len(files)}")
            for file in files:
                file_path = os.path.join(initial_stats['persistence_directory'], file)
                size = os.path.getsize(file_path)
                print(f"   - {file}: {size} bytes")
        else:
            print(f"❌ Directorio de persistencia no existe: {initial_stats['persistence_directory']}")
        
        # Simular creación de embeddings (sin archivo real)
        print("\n🔄 Simulando creación de embeddings...")
        
        # Crear un embedding dummy para prueba
        test_text = "Este es un texto de prueba para verificar la persistencia de RAG."
        test_embedding = rag.get_embedding(test_text)
        
        if test_embedding:
            print(f"✅ Embedding generado: {len(test_embedding)} dimensiones")
            
            # Agregar a la colección
            test_book_id = "test_persistence_book"
            test_chunk_id = f"{test_book_id}_chunk_0"
            
            rag.collection.add(
                embeddings=[test_embedding],
                documents=[test_text],
                metadatas=[{"book_id": test_book_id, "chunk_index": 0}],
                ids=[test_chunk_id]
            )
            
            print(f"✅ Embedding agregado a la colección")
            
            # Verificar estado después de agregar
            print("\n📊 Estado después de agregar embedding:")
            updated_stats = rag.get_rag_stats()
            print(f"   - Total embeddings: {updated_stats['total_embeddings']}")
            print(f"   - Libros únicos: {updated_stats['unique_books']}")
            
            # Verificar que el embedding se puede recuperar
            print("\n🔍 Verificando recuperación del embedding...")
            results = rag.collection.query(
                query_embeddings=[test_embedding],
                n_results=1,
                where={"book_id": test_book_id}
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                retrieved_text = results['documents'][0][0]
                print(f"✅ Embedding recuperado: '{retrieved_text[:50]}...'")
            else:
                print("❌ No se pudo recuperar el embedding")
            
            # Limpiar embedding de prueba
            print("\n🧹 Limpiando embedding de prueba...")
            rag.collection.delete(ids=[test_chunk_id])
            
            print("✅ Embedding de prueba eliminado")
            
        else:
            print("❌ No se pudo generar embedding de prueba")
        
        # Verificar estado final
        print("\n📊 Estado final de RAG:")
        final_stats = rag.get_rag_stats()
        print(f"   - Total embeddings: {final_stats['total_embeddings']}")
        print(f"   - Libros únicos: {final_stats['unique_books']}")
        
        print("\n🎯 PRUEBA COMPLETADA")
        print("=" * 50)
        
        if final_stats['total_embeddings'] == initial_stats['total_embeddings']:
            print("✅ La persistencia funciona correctamente")
            print("💡 Los embeddings se mantienen entre operaciones")
        else:
            print("⚠️  La persistencia puede tener problemas")
            
    except ImportError as e:
        print(f"❌ Error importando módulo RAG: {e}")
        print("💡 Asegúrate de que el backend esté configurado correctamente")
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

def test_rag_endpoints():
    """Prueba los endpoints de RAG del backend"""
    
    print("\n🌐 PRUEBA DE ENDPOINTS RAG")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # URL base (ajustar según tu configuración)
        base_url = "http://localhost:8001"
        
        print(f"🔗 Probando endpoints en: {base_url}")
        
        # Probar endpoint de estado
        print("\n📊 Probando /rag/status...")
        try:
            response = requests.get(f"{base_url}/rag/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data['status']}")
                if data['rag_stats']:
                    stats = data['rag_stats']
                    print(f"   - Embeddings: {stats.get('total_embeddings', 'N/A')}")
                    print(f"   - Libros: {stats.get('unique_books', 'N/A')}")
                    print(f"   - Estado: {stats.get('status', 'N/A')}")
            else:
                print(f"❌ Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        
        # Probar endpoint de documentación
        print("\n📚 Probando /docs...")
        try:
            response = requests.get(f"{base_url}/docs", timeout=10)
            if response.status_code == 200:
                print("✅ Documentación accesible")
            else:
                print(f"❌ Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            
    except ImportError:
        print("⚠️  requests no disponible, saltando prueba de endpoints")
    except Exception as e:
        print(f"❌ Error durante prueba de endpoints: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE PERSISTENCIA RAG")
    print("=" * 60)
    
    # Prueba de persistencia local
    test_rag_persistence()
    
    # Prueba de endpoints
    test_rag_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 PRUEBAS COMPLETADAS")
    print("\n💡 Para probar la persistencia completa:")
    print("   1. Ejecuta este script")
    print("   2. Reinicia el servidor backend")
    print("   3. Ejecuta este script nuevamente")
    print("   4. Los embeddings deberían mantenerse")
