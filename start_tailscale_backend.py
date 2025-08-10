#!/usr/bin/env python3
"""
Script para iniciar el backend de Biblioteca Inteligente con configuración segura para Tailscale
"""
import os
import sys
import time
import uvicorn
from pathlib import Path

# Agregar el directorio del backend al path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Importar configuración de Tailscale
from tailscale_config import get_secure_config_for_tailscale, generate_tailscale_ssl_cert

def start_secure_backend():
    """
    Inicia el backend con configuración segura para Tailscale
    """
    print("🚀 Iniciando Biblioteca Inteligente - Backend Seguro con Tailscale")
    print("=" * 70)
    
    # Obtener configuración de Tailscale
    config = get_secure_config_for_tailscale()
    if not config:
        print("❌ No se pudo obtener configuración de Tailscale")
        print("💡 Asegúrate de que Tailscale esté instalado y conectado")
        print("   1. Abre la aplicación de Tailscale")
        print("   2. Inicia sesión si no lo has hecho")
        print("   3. Asegúrate de que esté conectado")
        return False
    
    tailscale_ip = config['host']
    port = config['port']
    
    print(f"🌐 IP de Tailscale: {tailscale_ip}")
    print(f"🔌 Puerto: {port}")
    print(f"🔒 SSL: {'Habilitado' if config['use_ssl'] else 'Deshabilitado'}")
    
    # Configurar certificados SSL para Tailscale
    if config['use_ssl']:
        print("\n🔒 Configurando SSL...")
        
        # Usar certificados existentes o generar nuevos
        cert_file = str(backend_dir / "ssl" / "tailscale_cert.pem")
        key_file = str(backend_dir / "ssl" / "tailscale_key.pem")
        
        # Verificar si existen, si no generarlos
        if not Path(cert_file).exists() or not Path(key_file).exists():
            cert_file, key_file = generate_tailscale_ssl_cert(tailscale_ip)
            if not cert_file or not key_file:
                print("❌ Error generando certificados SSL")
                return False
        
        ssl_config = {
            "ssl_certfile": cert_file,
            "ssl_keyfile": key_file,
        }
    else:
        ssl_config = {}
    
    # Cambiar al directorio del backend
    os.chdir(backend_dir)
    
    # Configuración del servidor
    server_config = {
        "app": "main:app",
        "host": tailscale_ip,  # Usar IP específica de Tailscale
        "port": port,
        "reload": True,
        "log_level": "info",
        "access_log": True,
        "use_colors": True,
        "loop": "asyncio"
    }
    
    # Agregar configuración SSL si está habilitada
    if ssl_config:
        server_config.update(ssl_config)
        protocol = "https"
    else:
        protocol = "http"
    
    print(f"\n✅ Configuración completada")
    print(f"🌐 URL del backend: {protocol}://{tailscale_ip}:{port}")
    print(f"📱 Accesible desde cualquier dispositivo en tu red Tailscale")
    print(f"⏹️  Presiona Ctrl+C para detener el servidor")
    print("-" * 70)
    
    try:
        # Iniciar el servidor
        uvicorn.run(**server_config)
        
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido por el usuario")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        print("💡 Verifica que:")
        print("   - Tailscale esté conectado")
        print("   - El puerto no esté en uso")
        print("   - Tengas permisos para usar el puerto")
        return False

if __name__ == "__main__":
    success = start_secure_backend()
    if not success:
        sys.exit(1)
