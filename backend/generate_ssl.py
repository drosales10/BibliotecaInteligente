#!/usr/bin/env python3
"""
Script para generar certificados SSL para el backend
Ejecutar antes de iniciar el servidor para habilitar HTTPS
"""

import os
import sys
import subprocess
from pathlib import Path

def check_openssl():
    """Verifica si OpenSSL está disponible"""
    try:
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ OpenSSL encontrado: {result.stdout.strip()}")
            return True
        else:
            print("❌ OpenSSL no está disponible")
            return False
    except FileNotFoundError:
        print("❌ OpenSSL no está instalado")
        print("💡 Instala OpenSSL desde: https://slproweb.com/products/Win32OpenSSL.html")
        return False

def create_ssl_directory():
    """Crea el directorio SSL si no existe"""
    ssl_dir = Path("ssl")
    if not ssl_dir.exists():
        ssl_dir.mkdir()
        print("📁 Directorio SSL creado")
    else:
        print("📁 Directorio SSL ya existe")
    return ssl_dir

def generate_private_key(ssl_dir):
    """Genera la clave privada RSA"""
    key_file = ssl_dir / "key.pem"
    
    if key_file.exists():
        print("🔑 Clave privada ya existe")
        return True
    
    try:
        print("🔑 Generando clave privada RSA...")
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True, capture_output=True)
        print("✅ Clave privada generada exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando clave privada: {e}")
        return False

def generate_certificate(ssl_dir):
    """Genera el certificado autofirmado"""
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    if cert_file.exists():
        print("📜 Certificado ya existe")
        return True
    
    try:
        print("📜 Generando certificado autofirmado...")
        subprocess.run([
            "openssl", "req", "-new", "-x509", 
            "-key", str(key_file), 
            "-out", str(cert_file), 
            "-days", "365", 
            "-subj", "/C=ES/ST=Madrid/L=Madrid/O=Biblioteca Inteligente/CN=localhost"
        ], check=True, capture_output=True)
        print("✅ Certificado autofirmado generado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generando certificado: {e}")
        return False

def verify_ssl_files(ssl_dir):
    """Verifica que los archivos SSL se crearon correctamente"""
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print("✅ Verificación SSL completada:")
        print(f"   📜 Certificado: {cert_file}")
        print(f"   🔑 Clave privada: {key_file}")
        return True
    else:
        print("❌ Error: No se pudieron crear todos los archivos SSL")
        return False

def main():
    """Función principal"""
    print("🔒 Generador de Certificados SSL para Biblioteca Inteligente")
    print("=" * 60)
    
    # Verificar OpenSSL
    if not check_openssl():
        print("\n💡 Soluciones:")
        print("   1. Instala OpenSSL desde https://slproweb.com/products/Win32OpenSSL.html")
        print("   2. Agrega OpenSSL al PATH del sistema")
        print("   3. Reinicia la terminal después de la instalación")
        return False
    
    # Crear directorio SSL
    ssl_dir = create_ssl_directory()
    
    # Generar clave privada
    if not generate_private_key(ssl_dir):
        return False
    
    # Generar certificado
    if not generate_certificate(ssl_dir):
        return False
    
    # Verificar archivos
    if not verify_ssl_files(ssl_dir):
        return False
    
    print("\n🎉 Certificados SSL generados exitosamente!")
    print("📱 Ahora puedes acceder desde dispositivos móviles usando HTTPS")
    print("🔗 URL: https://192.168.100.6:8001")
    print("\n⚠️  Nota: Los navegadores mostrarán una advertencia de seguridad")
    print("   porque es un certificado autofirmado. Esto es normal en desarrollo.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Proceso completado exitosamente")
        else:
            print("\n❌ Proceso falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
