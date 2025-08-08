#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones SSL en Google Drive Manager
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ssl_fixes():
    """Prueba las correcciones SSL implementadas"""
    try:
        logger.info("🔍 Iniciando pruebas de correcciones SSL...")
        
        # Importar el módulo de Google Drive Manager
        from google_drive_manager import GoogleDriveManager
        
        # Crear instancia del manager
        drive_manager = GoogleDriveManager()
        
        # Intentar inicializar el servicio
        logger.info("🔍 Inicializando servicio de Google Drive...")
        drive_manager.initialize_service()
        
        if not drive_manager.service:
            logger.error("❌ No se pudo inicializar el servicio de Google Drive")
            return False
        
        logger.info("✅ Servicio de Google Drive inicializado correctamente")
        
        # Probar la función get_or_create_category_folder
        logger.info("🔍 Probando get_or_create_category_folder...")
        try:
            category_folder_id = drive_manager.get_or_create_category_folder("Test Category")
            if category_folder_id:
                logger.info(f"✅ Carpeta de categoría creada/encontrada: {category_folder_id}")
            else:
                logger.error("❌ No se pudo crear/encontrar la carpeta de categoría")
                return False
        except Exception as e:
            logger.error(f"❌ Error en get_or_create_category_folder: {e}")
            return False
        
        # Probar la función get_letter_folder
        logger.info("🔍 Probando get_letter_folder...")
        try:
            letter_folder_id = drive_manager.get_letter_folder(category_folder_id, "Test Book Title")
            if letter_folder_id:
                logger.info(f"✅ Carpeta de letra creada/encontrada: {letter_folder_id}")
            else:
                logger.error("❌ No se pudo crear/encontrar la carpeta de letra")
                return False
        except Exception as e:
            logger.error(f"❌ Error en get_letter_folder: {e}")
            return False
        
        logger.info("🎉 Todas las pruebas SSL pasaron exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error general en las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = test_ssl_fixes()
    if success:
        logger.info("✅ Correcciones SSL verificadas correctamente")
        sys.exit(0)
    else:
        logger.error("❌ Las correcciones SSL no funcionan correctamente")
        sys.exit(1) 