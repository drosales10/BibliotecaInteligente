#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de sincronización con Google Drive
"""

import os
import sys
import traceback
from pathlib import Path

def check_environment():
    """Verifica el entorno básico"""
    print("🔍 VERIFICANDO ENTORNO BÁSICO")
    print("=" * 50)
    
    # Verificar archivos de credenciales
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    
    print(f"📁 Credentials file: {'✅ Existe' if os.path.exists(credentials_file) else '❌ No existe'}")
    print(f"📁 Token file: {'✅ Existe' if os.path.exists(token_file) else '❌ No existe'}")
    
    # Verificar variables de entorno
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"🔑 GEMINI_API_KEY: {'✅ Configurada' if gemini_key and gemini_key != 'tu_clave_api_aqui' else '❌ No configurada'}")
    
    # Verificar directorio de trabajo
    print(f"📂 Directorio actual: {os.getcwd()}")
    
    return os.path.exists(credentials_file) and os.path.exists(token_file)

def check_google_drive_manager():
    """Verifica el Google Drive Manager"""
    print("\n🔍 VERIFICANDO GOOGLE DRIVE MANAGER")
    print("=" * 50)
    
    try:
        from google_drive_manager import get_drive_manager
        print("✅ Importación exitosa de google_drive_manager")
        
        # Intentar obtener la instancia
        try:
            drive_manager = get_drive_manager()
            print("✅ Instancia de drive_manager obtenida")
            
            # Verificar atributos básicos
            print(f"🔧 Service: {'✅ Configurado' if drive_manager.service else '❌ No configurado'}")
            print(f"🔧 Root folder ID: {'✅ Configurado' if drive_manager.root_folder_id else '❌ No configurado'}")
            
            return drive_manager
            
        except Exception as e:
            print(f"❌ Error al obtener drive_manager: {e}")
            traceback.print_exc()
            return None
            
    except ImportError as e:
        print(f"❌ Error al importar google_drive_manager: {e}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        traceback.print_exc()
        return None

def check_drive_health(drive_manager):
    """Verifica la salud de Google Drive"""
    print("\n🔍 VERIFICANDO SALUD DE GOOGLE DRIVE")
    print("=" * 50)
    
    if not drive_manager:
        print("❌ No hay drive_manager disponible")
        return False
    
    try:
        # Verificar conexión básica
        print("🔄 Verificando conexión básica...")
        drive_manager._ensure_service_connection()
        print("✅ Conexión básica establecida")
        
        # Verificar health check
        print("🔄 Ejecutando health check...")
        health_result = drive_manager.health_check()
        print(f"📊 Health check resultado: {health_result}")
        
        if health_result['status'] == 'healthy':
            print("✅ Google Drive está funcionando correctamente")
            return True
        else:
            print(f"❌ Google Drive no está saludable: {health_result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        traceback.print_exc()
        return False

def test_file_upload(drive_manager):
    """Prueba la subida de un archivo"""
    print("\n🔍 PROBANDO SUBIDA DE ARCHIVO")
    print("=" * 50)
    
    if not drive_manager:
        print("❌ No hay drive_manager disponible")
        return False
    
    # Crear un archivo de prueba
    test_file_path = "test_upload.txt"
    try:
        with open(test_file_path, 'w') as f:
            f.write("Este es un archivo de prueba para verificar la funcionalidad de Google Drive")
        
        print(f"📝 Archivo de prueba creado: {test_file_path}")
        
        # Intentar subir el archivo
        print("🔄 Intentando subir archivo de prueba...")
        result = drive_manager.upload_book_to_drive(
            test_file_path,
            "Libro de Prueba",
            "Autor de Prueba",
            "Test"
        )
        
        print(f"📊 Resultado de la subida: {result}")
        
        if result['success']:
            print("✅ Subida de archivo exitosa")
            
            # Limpiar archivo de prueba
            try:
                os.remove(test_file_path)
                print("🧹 Archivo de prueba eliminado")
            except:
                pass
                
            return True
        else:
            print(f"❌ Error en la subida: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba de subida: {e}")
        traceback.print_exc()
        
        # Limpiar archivo de prueba
        try:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        except:
            pass
            
        return False

def check_crud_functions():
    """Verifica las funciones CRUD necesarias"""
    print("\n🔍 VERIFICANDO FUNCIONES CRUD")
    print("=" * 50)
    
    try:
        import crud
        print("✅ Módulo crud importado correctamente")
        
        # Verificar funciones específicas
        required_functions = [
            'get_book',
            'update_book_sync_status'
        ]
        
        for func_name in required_functions:
            if hasattr(crud, func_name):
                print(f"✅ Función {func_name} disponible")
            else:
                print(f"❌ Función {func_name} no disponible")
                
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar crud: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en crud: {e}")
        return False

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    print("\n🔍 VERIFICANDO CONEXIÓN A BASE DE DATOS")
    print("=" * 50)
    
    try:
        import database
        from sqlalchemy import text
        print("✅ Módulo database importado correctamente")
        
        # Verificar conexión usando SessionLocal directamente
        db = database.SessionLocal()
        print("✅ Conexión a base de datos establecida")
        
        # Verificar que podemos ejecutar una consulta simple
        result = db.execute(text("SELECT 1"))
        print("✅ Consulta de prueba ejecutada correctamente")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en conexión a base de datos: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO DE SINCRONIZACIÓN CON GOOGLE DRIVE")
    print("=" * 60)
    
    # Verificar entorno
    env_ok = check_environment()
    
    # Verificar Google Drive Manager
    drive_manager = check_google_drive_manager()
    
    # Verificar salud de Drive
    drive_healthy = False
    if drive_manager:
        drive_healthy = check_drive_health(drive_manager)
    
    # Verificar funciones CRUD
    crud_ok = check_crud_functions()
    
    # Verificar base de datos
    db_ok = check_database_connection()
    
    # Probar subida de archivo
    upload_ok = False
    if drive_healthy:
        upload_ok = test_file_upload(drive_manager)
    
    # Resumen final
    print("\n📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 50)
    print(f"🔧 Entorno: {'✅ OK' if env_ok else '❌ PROBLEMA'}")
    print(f"🔧 Drive Manager: {'✅ OK' if drive_manager else '❌ PROBLEMA'}")
    print(f"🔧 Salud de Drive: {'✅ OK' if drive_healthy else '❌ PROBLEMA'}")
    print(f"🔧 Funciones CRUD: {'✅ OK' if crud_ok else '❌ PROBLEMA'}")
    print(f"🔧 Base de datos: {'✅ OK' if db_ok else '❌ PROBLEMA'}")
    print(f"🔧 Subida de archivos: {'✅ OK' if upload_ok else '❌ PROBLEMA'}")
    
    if all([env_ok, drive_manager, drive_healthy, crud_ok, db_ok, upload_ok]):
        print("\n✅ TODOS LOS COMPONENTES ESTÁN FUNCIONANDO CORRECTAMENTE")
        print("La sincronización debería funcionar sin problemas")
    else:
        print("\n❌ SE DETECTARON PROBLEMAS")
        print("Revisa los errores anteriores para identificar la causa")
        
        if not env_ok:
            print("\n💡 SOLUCIÓN: Configura las credenciales de Google Drive")
            print("   - Asegúrate de que credentials.json y token.json existan")
            
        if not drive_healthy:
            print("\n💡 SOLUCIÓN: Verifica la configuración de Google Drive")
            print("   - Revisa los permisos de la API")
            print("   - Verifica la conexión a internet")
            
        if not crud_ok or not db_ok:
            print("\n💡 SOLUCIÓN: Verifica la base de datos")
            print("   - Asegúrate de que las migraciones estén aplicadas")
            print("   - Verifica la conexión a la base de datos")

if __name__ == "__main__":
    main()
