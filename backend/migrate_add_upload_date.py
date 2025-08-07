#!/usr/bin/env python3
"""
Script de migración para agregar el campo upload_date a la tabla books
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_upload_date():
    """Agrega el campo upload_date a la tabla books existente"""
    
    # Ruta de la base de datos
    db_path = "../library.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada. Creando nueva base de datos...")
        return
    
    print("🔧 Iniciando migración para agregar campo upload_date...")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si el campo ya existe
        cursor.execute("PRAGMA table_info(books)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'upload_date' in columns:
            print("✅ Campo upload_date ya existe en la tabla books")
            return
        
        print("📝 Agregando campo upload_date a la tabla books...")
        
        # Agregar el campo upload_date con valor por defecto
        current_time = datetime.now().isoformat()
        cursor.execute("""
            ALTER TABLE books 
            ADD COLUMN upload_date DATETIME
        """)
        
        # Actualizar registros existentes con la fecha actual
        cursor.execute("""
            UPDATE books 
            SET upload_date = ? 
            WHERE upload_date IS NULL
        """, (current_time,))
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar que se agregó correctamente
        cursor.execute("PRAGMA table_info(books)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'upload_date' in columns:
            print("✅ Campo upload_date agregado exitosamente")
            
            # Contar registros actualizados
            cursor.execute("SELECT COUNT(*) FROM books")
            count = cursor.fetchone()[0]
            print(f"📊 {count} registros actualizados con fecha de carga")
        else:
            print("❌ Error: No se pudo agregar el campo upload_date")
            
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_upload_date() 