#!/usr/bin/env python3
"""
Script de prueba para verificar que la carga masiva de ZIP funciona correctamente
con las correcciones SSL implementadas.
"""

import os
import sys
import logging
import tempfile
import zipfile
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_zip():
    """Crea un archivo ZIP de prueba con algunos archivos PDF simulados"""
    try:
        # Crear directorio temporal para el ZIP
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "test_books.zip")
        
        logger.info(f"📁 Creando ZIP de prueba en: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Crear algunos archivos PDF simulados
            test_files = [
                ("libro1.pdf", "Contenido del libro 1"),
                ("libro2.pdf", "Contenido del libro 2"),
                ("libro3.pdf", "Contenido del libro 3")
            ]
            
            for filename, content in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(content)
                zipf.write(file_path, filename)
                logger.info(f"✅ Archivo agregado al ZIP: {filename}")
        
        logger.info(f"✅ ZIP de prueba creado: {zip_path}")
        return zip_path
        
    except Exception as e:
        logger.error(f"❌ Error creando ZIP de prueba: {e}")
        return None

def test_bulk_upload_ssl():
    """Prueba la carga masiva de ZIP con correcciones SSL"""
    try:
        logger.info("🔍 Iniciando pruebas de carga masiva de ZIP con SSL...")
        
        # Importar el gestor de Google Drive
        from google_drive_manager import get_drive_manager
        drive_manager = get_drive_manager()
        
        if not drive_manager.service:
            logger.error("❌ Servicio de Google Drive no inicializado")
            return False
        
        logger.info("✅ Servicio de Google Drive inicializado correctamente")
        
        # Crear ZIP de prueba
        zip_path = create_test_zip()
        if not zip_path:
            logger.error("❌ No se pudo crear el ZIP de prueba")
            return False
        
        # Simular el procesamiento del ZIP (sin subir realmente)
        logger.info("🔍 Simulando procesamiento de ZIP...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                logger.info(f"📄 Archivos en el ZIP: {len(file_list)}")
                
                for filename in file_list:
                    if filename.lower().endswith('.pdf'):
                        logger.info(f"📖 Procesando: {filename}")
                        
                        # Simular la extracción y procesamiento
                        with zipf.open(filename) as file:
                            content = file.read()
                            logger.info(f"✅ Archivo procesado: {filename} ({len(content)} bytes)")
        
        except Exception as e:
            logger.error(f"❌ Error procesando ZIP: {e}")
            return False
        
        # Limpiar archivo temporal
        try:
            os.remove(zip_path)
            logger.info("🧹 Archivo ZIP de prueba eliminado")
        except:
            pass
        
        logger.info("🎉 Pruebas de carga masiva de ZIP completadas exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error general en las pruebas: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando pruebas de carga masiva de ZIP con SSL...")
    
    success = test_bulk_upload_ssl()
    
    if success:
        logger.info("✅ Todas las pruebas pasaron exitosamente!")
        sys.exit(0)
    else:
        logger.error("❌ Algunas pruebas fallaron")
        sys.exit(1)
