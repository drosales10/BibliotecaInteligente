#!/usr/bin/env python3
"""
Script completo para resetear la biblioteca
1. Elimina todos los libros de la base de datos
2. Limpia portadas huérfanas
3. Prepara el sistema para empezar desde cero
"""

import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def reset_library():
    """Resetea completamente la biblioteca"""
    
    print("🔄 RESETEO COMPLETO DE LA BIBLIOTECA")
    print("=" * 60)
    print("⚠️  ADVERTENCIA: ESTA ACCIÓN ELIMINARÁ TODOS LOS LIBROS")
    print("• Todos los registros de libros serán eliminados")
    print("• Las portadas huérfanas serán eliminadas")
    print("• Los archivos físicos de libros se mantendrán")
    print("• ESTA ACCIÓN NO SE PUEDE DESHACER")
    print("=" * 60)
    
    # Confirmación del usuario
    confirm = input("¿Estás seguro de que quieres continuar? (escribe 'RESETEAR' para confirmar): ")
    
    if confirm != "RESETEAR":
        print("❌ Operación cancelada")
        return
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # PASO 1: Contar libros antes de eliminar
        total_books = db.query(models.Book).count()
        print(f"📊 PASO 1: Total de libros a eliminar: {total_books}")
        
        if total_books == 0:
            print("✅ No hay libros para eliminar")
        else:
            # Eliminar todos los libros
            deleted_count = db.query(models.Book).delete()
            db.commit()
            print(f"✅ {deleted_count} libros eliminados exitosamente")
        
        # PASO 2: Limpiar portadas huérfanas
        print("\n📁 PASO 2: Limpiando portadas huérfanas...")
        
        covers_dir = os.path.join("static", "covers")
        if os.path.exists(covers_dir):
            # Contar archivos antes de limpiar
            total_files = 0
            for filename in os.listdir(covers_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    total_files += 1
            
            print(f"📊 Archivos de portada encontrados: {total_files}")
            
            if total_files > 0:
                # Como no hay libros, todos los archivos son huérfanos
                deleted_count = 0
                total_size_freed = 0
                
                for filename in os.listdir(covers_dir):
                    if filename.endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            file_path = os.path.join(covers_dir, filename)
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size_freed += file_size
                            print(f"🗑️ Eliminado: {filename} ({round(file_size / (1024 * 1024), 2)} MB)")
                        except Exception as e:
                            print(f"❌ Error eliminando {filename}: {e}")
                
                print(f"✅ {deleted_count} portadas eliminadas")
                print(f"💾 {round(total_size_freed / (1024 * 1024), 2)} MB liberados")
            else:
                print("✅ No hay archivos de portada para eliminar")
        else:
            print("✅ Directorio de portadas no existe")
        
        # PASO 3: Verificar estado final
        print("\n📊 PASO 3: Verificando estado final...")
        
        remaining_books = db.query(models.Book).count()
        print(f"📚 Libros restantes en BD: {remaining_books}")
        
        if os.path.exists(covers_dir):
            remaining_files = 0
            for filename in os.listdir(covers_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    remaining_files += 1
            print(f"🖼️ Archivos de portada restantes: {remaining_files}")
        else:
            print("🖼️ Directorio de portadas: No existe")
        
        print("\n🎉 RESETEO COMPLETADO EXITOSAMENTE")
        print("=" * 40)
        print("✅ La biblioteca está lista para empezar desde cero")
        print("✅ Puedes comenzar a cargar libros nuevamente")
        print("✅ Todas las portadas se guardarán localmente")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el reseteo: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reset_library()
