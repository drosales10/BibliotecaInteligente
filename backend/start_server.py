import uvicorn
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv(dotenv_path='../.env')

def get_config():
    """Obtiene la configuración desde variables de entorno o usa valores por defecto"""
    host = os.getenv("HOST", "0.0.0.0").strip().strip('"').strip("'")
    port = int(os.getenv("PORT", 8001))
    log_level = os.getenv("LOG_LEVEL", "info").strip().strip('"').strip("'").lower()
    reload = os.getenv("RELOAD", "true").strip().strip('"').strip("'").lower() == "true"
    use_ssl = os.getenv("USE_SSL", "true").strip().strip('"').strip("'").lower() == "true"
    
    return host, port, log_level, reload, use_ssl

def get_ssl_config():
    """Obtiene la configuración SSL si está habilitada"""
    try:
        from ssl_config import get_ssl_config as get_ssl
        ssl_config = get_ssl()
        
        if ssl_config and ssl_config.get("ssl_certfile") and ssl_config.get("ssl_keyfile"):
            print("🔒 Configuración SSL detectada")
            return ssl_config
        else:
            print("⚠️  SSL habilitado pero no se encontraron certificados")
            return {}
            
    except ImportError:
        print("⚠️  Módulo SSL no disponible")
        return {}
    except Exception as e:
        print(f"⚠️  Error configurando SSL: {e}")
        return {}

if __name__ == "__main__":
    host, port, log_level, reload, use_ssl = get_config()
    
    print("🚀 Iniciando servidor de la librería inteligente...")
    print(f"📍 Host: {host}")
    print(f"🔌 Puerto: {port}")
    print(f"📝 Log Level: {log_level}")
    print(f"🔄 Reload: {reload}")
    print(f"🔒 SSL: {use_ssl}")
    print("⏹️  Presiona Ctrl+C para detener el servidor")
    print("")
    
    # Configuración del servidor
    server_config = {
        "app": "main:app",
        "host": host,
        "port": port,
        "reload": reload,
        "log_level": log_level,
        "access_log": True,
        "use_colors": True,
        "loop": "asyncio"
    }
    
    # Agregar configuración SSL si está habilitada
    if use_ssl:
        ssl_config = get_ssl_config()
        if ssl_config:
            server_config.update(ssl_config)
            print("✅ Servidor iniciando con HTTPS")
        else:
            print("⚠️  SSL habilitado pero no configurado, iniciando con HTTP")
    
    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        print("💡 Verifica que el puerto no esté en uso y que tengas permisos")
        sys.exit(1) 