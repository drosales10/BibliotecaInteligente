"""
Configuración específica para Tailscale
Permite acceso seguro desde dispositivos móviles a través de la red privada de Tailscale
"""
import subprocess
import re
import os
import sys
from pathlib import Path

def get_tailscale_ip():
    """
    Obtiene la dirección IP de Tailscale asignada a este dispositivo
    """
    try:
        # Intentar obtener la IP usando el comando de Tailscale
        result = subprocess.run([
            "C:\\Program Files\\Tailscale\\tailscale.exe", "ip", "-4"
        ], capture_output=True, text=True, check=True)
        
        tailscale_ip = result.stdout.strip()
        if tailscale_ip and not tailscale_ip.startswith("no current"):
            print(f"🌐 IP de Tailscale detectada: {tailscale_ip}")
            return tailscale_ip
        else:
            print("⚠️  Tailscale no está conectado o no tiene IP asignada")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo IP de Tailscale: {e}")
        return None
    except FileNotFoundError:
        print("❌ Tailscale no está instalado o no está en la ruta esperada")
        return None

def check_tailscale_status():
    """
    Verifica el estado de conexión de Tailscale
    """
    try:
        result = subprocess.run([
            "C:\\Program Files\\Tailscale\\tailscale.exe", "status"
        ], capture_output=True, text=True, check=True)
        
        status_output = result.stdout.strip()
        
        if "Tailscale is starting" in status_output:
            return "starting"
        elif "logged out" in status_output.lower():
            return "logged_out"
        elif len(status_output.split('\n')) > 2:  # Tiene dispositivos listados
            return "connected"
        else:
            return "disconnected"
            
    except subprocess.CalledProcessError:
        return "error"
    except FileNotFoundError:
        return "not_installed"

def ensure_tailscale_connection():
    """
    Asegura que Tailscale esté conectado antes de iniciar los servicios
    """
    print("🔍 Verificando conexión de Tailscale...")
    
    status = check_tailscale_status()
    
    if status == "not_installed":
        print("❌ Tailscale no está instalado")
        print("💡 Instala Tailscale desde: https://tailscale.com/download")
        return False
    
    elif status == "logged_out":
        print("🔐 Tailscale está instalado pero no has iniciado sesión")
        print("💡 Ejecuta: tailscale up")
        print("   O usa la aplicación gráfica de Tailscale")
        return False
    
    elif status == "starting":
        print("⏳ Tailscale está iniciando...")
        print("💡 Espera unos segundos y vuelve a intentar")
        return False
    
    elif status == "disconnected":
        print("🔌 Tailscale está instalado pero no conectado")
        try:
            print("🚀 Intentando conectar Tailscale...")
            subprocess.run([
                "C:\\Program Files\\Tailscale\\tailscale.exe", "up"
            ], check=True)
            print("✅ Conexión de Tailscale iniciada")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error conectando Tailscale")
            return False
    
    elif status == "connected":
        print("✅ Tailscale está conectado")
        return True
    
    else:
        print(f"⚠️  Estado de Tailscale desconocido: {status}")
        return False

def get_secure_config_for_tailscale():
    """
    Obtiene la configuración segura para usar con Tailscale
    """
    if not ensure_tailscale_connection():
        print("❌ No se puede configurar sin una conexión Tailscale activa")
        return None
    
    tailscale_ip = get_tailscale_ip()
    if not tailscale_ip:
        print("❌ No se pudo obtener la IP de Tailscale")
        return None
    
    return {
        "host": tailscale_ip,  # Usar IP de Tailscale en lugar de 0.0.0.0
        "port": 8001,
        "frontend_port": 3000,
        "use_ssl": True,
        "ssl_cert_subject": f"/C=ES/ST=Madrid/L=Madrid/O=Biblioteca Inteligente/CN={tailscale_ip}",
        "allowed_hosts": [tailscale_ip, "localhost", "127.0.0.1"]
    }

def generate_tailscale_ssl_cert(tailscale_ip):
    """
    Genera certificados SSL específicos para la IP de Tailscale
    """
    try:
        ssl_dir = Path("backend/ssl")
        ssl_dir.mkdir(exist_ok=True)
        
        cert_file = ssl_dir / "tailscale_cert.pem"
        key_file = ssl_dir / "tailscale_key.pem"
        
        print(f"🔒 Generando certificados SSL para Tailscale IP: {tailscale_ip}")
        
        # Generar clave privada
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True, capture_output=True)
        
        # Crear archivo de configuración para el certificado con SAN
        config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ES
ST = Madrid
L = Madrid
O = Biblioteca Inteligente
CN = {tailscale_ip}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
IP.1 = {tailscale_ip}
IP.2 = 127.0.0.1
DNS.1 = localhost
"""
        
        config_file = ssl_dir / "tailscale_cert.conf"
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Generar certificado con SAN
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(key_file), 
            "-out", str(cert_file), "-days", "365", 
            "-config", str(config_file), "-extensions", "v3_req"
        ], check=True, capture_output=True)
        
        # Limpiar archivo temporal
        config_file.unlink()
        
        print("✅ Certificados SSL para Tailscale generados exitosamente")
        print(f"🔑 Certificado: {cert_file}")
        print(f"🔑 Clave privada: {key_file}")
        
        return str(cert_file), str(key_file)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando certificados SSL: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None, None

if __name__ == "__main__":
    # Verificar estado de Tailscale
    config = get_secure_config_for_tailscale()
    if config:
        print("✅ Configuración de Tailscale lista:")
        print(f"   Host: {config['host']}")
        print(f"   Puerto Backend: {config['port']}")
        print(f"   Puerto Frontend: {config['frontend_port']}")
        print(f"   SSL: {config['use_ssl']}")
        
        # Generar certificados si es necesario
        tailscale_ip = config['host']
        cert_file, key_file = generate_tailscale_ssl_cert(tailscale_ip)
        
        if cert_file and key_file:
            print(f"🌐 Tu aplicación estará disponible en: https://{tailscale_ip}:{config['port']}")
            print("📱 Podrás acceder desde cualquier dispositivo en tu red Tailscale")
    else:
        print("❌ No se pudo configurar Tailscale")
        sys.exit(1)
