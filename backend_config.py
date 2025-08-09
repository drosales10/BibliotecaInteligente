#!/usr/bin/env python3
"""
Script de configuración temporal para el backend
"""
import os
import sys

# Configuración del servidor
HOST = "0.0.0.0"  # Escuchar en todas las interfaces
PORT = 8001
LOG_LEVEL = "info"
RELOAD = True

# Crear archivo .env temporal en el directorio backend
env_content = f"""# Configuración temporal del backend
HOST={HOST}
PORT={PORT}
LOG_LEVEL={LOG_LEVEL}
RELOAD={str(RELOAD).lower()}
GEMINI_API_KEY=dummy_key
DATABASE_URL=sqlite:///../library.db
"""

backend_dir = "backend"
env_file = os.path.join(backend_dir, ".env")

try:
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"✅ Archivo de configuración creado: {env_file}")
    print(f"   Host: {HOST}")
    print(f"   Puerto: {PORT}")
    print(f"   Log Level: {LOG_LEVEL}")
    print(f"   Reload: {RELOAD}")
except Exception as e:
    print(f"❌ Error al crear archivo de configuración: {e}")
    sys.exit(1)

print("\n🚀 Para iniciar el backend, ejecuta:")
print(f"   cd {backend_dir}")
print("   python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload")
print("\n📱 El frontend se conectará automáticamente a http://localhost:8001")
