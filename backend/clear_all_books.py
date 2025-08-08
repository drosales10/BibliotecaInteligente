#!/usr/bin/env python3
"""
Script para eliminar todos los libros de la base de datos
ÚSESE CON PRECAUCIÓN - ESTA ACCIÓN NO SE PUEDE DESHACER
"""

import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def clear_all_books():
    """Elimina todos los libros de la base de datos"""
    
    print("⚠️  ADVERTENCIA: ESTA ACCIÓN ELIMINARÁ TODOS LOS LIBROS")
    print("=" * 60)
    print("• Todos los registros de libros serán eliminados")
    print("• Los archivos físicos de libros se mantendrán")
    print("• Las portadas se mantendrán hasta que uses el botón de limpieza")
    print("• ESTA ACCIÓN NO SE PUEDE DESHACER")
    print("=" * 60)
    
    # Confirmación del usuario
    confirm = input("¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
    
    if confirm != "SI":
        print("❌ Operación cancelada")
        return
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Contar libros antes de eliminar
        total_books = db.query(models.Book).count()
        print(f"📊 Total de libros a eliminar: {total_books}")
        
        if total_books == 0:
            print("✅ No hay libros para eliminar")
            return
        
        # Eliminar todos los libros
        deleted_count = db.query(models.Book).delete()
        db.commit()
        
        print(f"✅ {deleted_count} libros eliminados exitosamente")
        print("📝 La base de datos está lista para empezar desde cero")
        
        # Verificar que no quedan libros
        remaining_books = db.query(models.Book).count()
        print(f"📊 Libros restantes en BD: {remaining_books}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al eliminar libros: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_books()
