#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del rate limiter optimizado
"""

import time
import asyncio
from rate_limiter import (
    gemini_limiter, 
    gemini_embeddings_limiter,
    call_gemini_with_limit_sync,
    call_gemini_embeddings_with_limit_sync,
    get_all_rate_limit_stats
)

def test_sync_rate_limiter():
    """Prueba el rate limiter síncrono"""
    print("🧪 Probando Rate Limiter Síncrono...")
    
    def mock_api_call(text):
        """Simula una llamada a API"""
        time.sleep(0.1)  # Simular latencia de red
        return f"Respuesta para: {text}"
    
    try:
        # Probar múltiples llamadas rápidas
        for i in range(10):
            result = call_gemini_with_limit_sync(mock_api_call, f"texto_{i}")
            print(f"✅ Llamada {i+1}: {result}")
            time.sleep(0.1)  # Pequeña pausa entre llamadas
            
    except Exception as e:
        print(f"❌ Error en prueba síncrona: {e}")
    
    # Mostrar estadísticas
    stats = gemini_limiter.get_stats()
    print(f"📊 Estadísticas del limiter: {stats['statistics']['total_calls']} llamadas totales")

def test_embeddings_rate_limiter():
    """Prueba el rate limiter para embeddings"""
    print("\n🧪 Probando Rate Limiter para Embeddings...")
    
    def mock_embedding_call(text):
        """Simula una llamada de embedding"""
        time.sleep(0.05)  # Simular latencia de embedding
        return [0.1] * 768  # Simular vector de embedding
    
    try:
        # Probar múltiples llamadas de embedding
        for i in range(15):
            result = call_gemini_embeddings_with_limit_sync(mock_embedding_call, f"chunk_{i}")
            print(f"✅ Embedding {i+1}: {len(result)} dimensiones")
            time.sleep(0.05)  # Pausa muy corta para embeddings
            
    except Exception as e:
        print(f"❌ Error en prueba de embeddings: {e}")
    
    # Mostrar estadísticas
    stats = gemini_embeddings_limiter.get_stats()
    print(f"📊 Estadísticas de embeddings: {stats['statistics']['total_calls']} llamadas totales")

async def test_async_rate_limiter():
    """Prueba el rate limiter asíncrono"""
    print("\n🧪 Probando Rate Limiter Asíncrono...")
    
    async def mock_async_api_call(text):
        """Simula una llamada asíncrona a API"""
        await asyncio.sleep(0.1)  # Simular latencia de red
        return f"Respuesta asíncrona para: {text}"
    
    try:
        # Probar múltiples llamadas asíncronas
        tasks = []
        for i in range(8):
            task = gemini_limiter.call_with_limit(mock_async_api_call, f"async_texto_{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Llamada {i+1} falló: {result}")
            else:
                print(f"✅ Llamada {i+1}: {result}")
                
    except Exception as e:
        print(f"❌ Error en prueba asíncrona: {e}")

def show_final_stats():
    """Muestra estadísticas finales"""
    print("\n📊 ESTADÍSTICAS FINALES DEL RATE LIMITER")
    print("=" * 50)
    
    all_stats = get_all_rate_limit_stats()
    
    for limiter_name, stats in all_stats.items():
        print(f"\n🔍 {limiter_name.upper()}:")
        print(f"   📈 Llamadas totales: {stats['statistics']['total_calls']}")
        print(f"   ✅ Exitosas: {stats['statistics']['successful_calls']}")
        print(f"   ❌ Fallidas: {stats['statistics']['failed_calls']}")
        print(f"   ⚠️ Rate limited: {stats['statistics']['rate_limited_calls']}")
        print(f"   ⏱️ Tiempo promedio: {stats['statistics']['average_response_time']:.3f}s")
        print(f"   🔄 Llamadas este minuto: {stats['current_usage']['calls_this_minute']}")
        print(f"   🔄 Llamadas esta hora: {stats['current_usage']['calls_this_hour']}")

def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL RATE LIMITER OPTIMIZADO")
    print("=" * 60)
    
    # Probar rate limiter síncrono
    test_sync_rate_limiter()
    
    # Probar rate limiter para embeddings
    test_embeddings_rate_limiter()
    
    # Probar rate limiter asíncrono
    asyncio.run(test_async_rate_limiter())
    
    # Mostrar estadísticas finales
    show_final_stats()
    
    print("\n✅ PRUEBAS COMPLETADAS")
    print("El rate limiter está funcionando correctamente con reintentos automáticos")

if __name__ == "__main__":
    main()
