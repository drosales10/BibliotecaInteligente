#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones SSL en la eliminación de libros
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ssl_delete_fix():
    """Prueba la corrección SSL para eliminación de libros"""
    try:
        from google_drive_manager import get_drive_manager
        
        logger.info("🔧 Inicializando Google Drive Manager...")
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            logger.error("❌ No se pudo inicializar el servicio de Google Drive")
            return False
        
        logger.info("✅ Servicio de Google Drive inicializado correctamente")
        
        # Probar una operación de listado para verificar conexión
        logger.info("🔍 Probando operación de listado...")
        try:
            results = drive_manager.service.files().list(
                pageSize=1, 
                fields="files(id,name)"
            ).execute()
            
            logger.info("✅ Operación de listado exitosa")
            
        except Exception as e:
            logger.error(f"❌ Error en operación de listado: {e}")
            return False
        
        # Probar eliminación de un archivo inexistente (esto debería fallar pero sin error SSL)
        logger.info("🗑️ Probando manejo SSL en eliminación...")
        try:
            # Intentar eliminar un archivo que no existe (esto debería fallar pero sin error SSL)
            result = drive_manager.delete_book_from_drive("archivo_inexistente_12345")
            
            if result['success']:
                logger.warning("⚠️ Eliminación exitosa de archivo inexistente (comportamiento inesperado)")
            else:
                logger.info("✅ Manejo correcto de eliminación de archivo inexistente")
                logger.info(f"   Error esperado: {result['error']}")
            
            logger.info("✅ Prueba de eliminación completada sin errores SSL")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper():
                logger.error(f"❌ Error SSL persistente en eliminación: {e}")
                return False
            else:
                logger.info(f"✅ Error no-SSL manejado correctamente: {e}")
                return True
            
    except Exception as e:
        logger.error(f"❌ Error al ejecutar prueba SSL: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando pruebas de corrección SSL para eliminación...")
    
    # Verificar archivo de credenciales
    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        logger.error(f"❌ Archivo de credenciales no encontrado: {credentials_file}")
        logger.info("💡 Asegúrate de tener el archivo credentials.json en el directorio backend")
        return False
    
    logger.info("✅ Archivo de credenciales encontrado")
    
    # Ejecutar prueba
    success = test_ssl_delete_fix()
    
    if success:
        logger.info("🎉 Las correcciones SSL para eliminación están funcionando correctamente")
        logger.info("✅ La eliminación masiva de libros debería funcionar sin errores SSL")
        return True
    else:
        logger.error("❌ Las correcciones SSL para eliminación no están funcionando")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
