"""
Configuración SSL para el backend de Biblioteca Inteligente
Permite conexiones HTTPS para dispositivos móviles
"""

import os
import ssl
from pathlib import Path

def get_ssl_context():
    """
    Crea un contexto SSL para el servidor
    Si no hay certificados, crea certificados autofirmados
    """
    try:
        # Verificar si existen certificados SSL
        cert_file = Path("ssl/cert.pem")
        key_file = Path("ssl/key.pem")
        
        if cert_file.exists() and key_file.exists():
            # Usar certificados existentes
            return {
                "ssl_certfile": str(cert_file),
                "ssl_keyfile": str(key_file),
                "ssl_ca_certs": None,
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_version": ssl.PROTOCOL_TLS_SERVER,
                "ssl_ciphers": "DEFAULT"
            }
        else:
            # Crear directorio SSL si no existe
            ssl_dir = Path("ssl")
            ssl_dir.mkdir(exist_ok=True)
            
            # Generar certificados autofirmados
            generate_self_signed_cert()
            
            return {
                "ssl_certfile": str(cert_file),
                "ssl_keyfile": str(key_file),
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_version": ssl.PROTOCOL_TLS_SERVER,
                "ssl_ciphers": "DEFAULT"
            }
            
    except Exception as e:
        print(f"⚠️  Advertencia SSL: {e}")
        print("📱 El servidor funcionará solo con HTTP (no recomendado para móviles)")
        return {}

def generate_self_signed_cert():
    """
    Genera certificados SSL autofirmados usando OpenSSL
    """
    try:
        import subprocess
        
        # Verificar si OpenSSL está disponible
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ OpenSSL no está disponible. Instala OpenSSL para generar certificados SSL.")
            return False
        
        # Generar clave privada
        subprocess.run([
            "openssl", "genrsa", "-out", "ssl/key.pem", "2048"
        ], check=True, capture_output=True)
        
        # Generar certificado autofirmado
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", "ssl/key.pem", 
            "-out", "ssl/cert.pem", "-days", "365", "-subj",
            "/C=ES/ST=Madrid/L=Madrid/O=Biblioteca Inteligente/CN=localhost"
        ], check=True, capture_output=True)
        
        print("✅ Certificados SSL autofirmados generados exitosamente")
        print("🔒 El servidor ahora soporta HTTPS")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando certificados SSL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado generando certificados SSL: {e}")
        return False

def get_ssl_config():
    """
    Retorna la configuración SSL completa
    """
    ssl_context = get_ssl_context()
    
    if ssl_context:
        return {
            "ssl_certfile": ssl_context.get("ssl_certfile"),
            "ssl_keyfile": ssl_context.get("ssl_keyfile"),
            "ssl_ca_certs": ssl_context.get("ssl_ca_certs"),
            "ssl_cert_reqs": ssl_context.get("ssl_cert_reqs"),
            "ssl_version": ssl_context.get("ssl_version"),
            "ssl_ciphers": ssl_context.get("ssl_ciphers")
        }
    else:
        return {}

if __name__ == "__main__":
    # Generar certificados si se ejecuta directamente
    generate_self_signed_cert()
