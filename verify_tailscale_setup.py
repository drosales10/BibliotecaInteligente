#!/usr/bin/env python3
"""
Script de verificación para la configuración de Tailscale
Verifica que todo esté listo para usar la Biblioteca Inteligente de forma segura
"""
import subprocess
import sys
import os
import json
import time
import requests
from pathlib import Path

def print_header():
    """Muestra el encabezado del script"""
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN TAILSCALE")
    print("🔒 Biblioteca Inteligente - Verificación de Seguridad")
    print("=" * 80)

def check_tailscale_installation():
    """Verifica si Tailscale está instalado"""
    print("\n1. 📦 Verificando instalación de Tailscale...")
    
    tailscale_path = Path("C:/Program Files/Tailscale/tailscale.exe")
    if tailscale_path.exists():
        print("   ✅ Tailscale está instalado")
        return True
    else:
        print("   ❌ Tailscale no está instalado")
        print("   💡 Instala desde: https://tailscale.com/download")
        return False

def check_tailscale_connection():
    """Verifica si Tailscale está conectado"""
    print("\n2. 🌐 Verificando conexión de Tailscale...")
    
    try:
        result = subprocess.run([
            "C:/Program Files/Tailscale/tailscale.exe", "status"
        ], capture_output=True, text=True, check=True)
        
        status_output = result.stdout.strip()
        
        if "Tailscale is starting" in status_output:
            print("   ⏳ Tailscale está iniciando...")
            return False
        elif "logged out" in status_output.lower():
            print("   🔐 Tailscale no ha iniciado sesión")
            return False
        elif len(status_output.split('\n')) > 2:
            print("   ✅ Tailscale está conectado")
            return True
        else:
            print("   ❌ Tailscale no está conectado")
            return False
            
    except subprocess.CalledProcessError:
        print("   ❌ Error verificando estado de Tailscale")
        return False

def get_tailscale_ip():
    """Obtiene la IP de Tailscale"""
    print("\n3. 🏠 Obteniendo IP de Tailscale...")
    
    try:
        result = subprocess.run([
            "C:/Program Files/Tailscale/tailscale.exe", "ip", "-4"
        ], capture_output=True, text=True, check=True)
        
        tailscale_ip = result.stdout.strip()
        if tailscale_ip and not tailscale_ip.startswith("no current"):
            print(f"   ✅ IP de Tailscale: {tailscale_ip}")
            return tailscale_ip
        else:
            print("   ❌ No se pudo obtener IP de Tailscale")
            return None
            
    except subprocess.CalledProcessError:
        print("   ❌ Error obteniendo IP de Tailscale")
        return None

def check_python_installation():
    """Verifica si Python está instalado"""
    print("\n4. 🐍 Verificando instalación de Python...")
    
    try:
        result = subprocess.run([
            "python", "--version"
        ], capture_output=True, text=True, check=True)
        
        version = result.stdout.strip()
        print(f"   ✅ {version}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Python no está instalado o no está en el PATH")
        return False

def check_node_installation():
    """Verifica si Node.js está instalado"""
    print("\n5. 📦 Verificando instalación de Node.js...")
    
    try:
        result = subprocess.run([
            "node", "--version"
        ], capture_output=True, text=True, check=True)
        
        version = result.stdout.strip()
        print(f"   ✅ Node.js {version}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Node.js no está instalado")
        print("   💡 Instala desde: https://nodejs.org")
        return False

def check_openssl_installation():
    """Verifica si OpenSSL está disponible"""
    print("\n6. 🔒 Verificando OpenSSL para certificados SSL...")
    
    try:
        result = subprocess.run([
            "openssl", "version"
        ], capture_output=True, text=True, check=True)
        
        version = result.stdout.strip()
        print(f"   ✅ {version}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ⚠️  OpenSSL no está disponible")
        print("   💡 Se usará HTTP en lugar de HTTPS")
        return False

def check_required_files():
    """Verifica que todos los archivos necesarios existan"""
    print("\n7. 📁 Verificando archivos de configuración...")
    
    required_files = [
        "tailscale_config.py",
        "start_tailscale_backend.py", 
        "start_tailscale_frontend.py",
        "start_tailscale_secure.py",
        "start_tailscale_secure.bat",
        "backend/main.py",
        "frontend/package.json"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} falta")
            all_exist = False
    
    return all_exist

def check_backend_dependencies():
    """Verifica las dependencias del backend"""
    print("\n8. 🔧 Verificando dependencias del backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("   ❌ Directorio backend no existe")
        return False
    
    requirements_file = backend_dir / "requirements.txt"
    if requirements_file.exists():
        print("   ✅ requirements.txt encontrado")
        
        # Verificar si el entorno virtual existe
        venv_dir = Path("venv")
        if venv_dir.exists():
            print("   ✅ Entorno virtual encontrado")
        else:
            print("   ⚠️  No hay entorno virtual")
            print("   💡 Considera crear uno: python -m venv venv")
        
        return True
    else:
        print("   ❌ requirements.txt no encontrado")
        return False

def check_frontend_dependencies():
    """Verifica las dependencias del frontend"""
    print("\n9. 🌐 Verificando dependencias del frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("   ❌ Directorio frontend no existe")
        return False
    
    package_json = frontend_dir / "package.json"
    node_modules = frontend_dir / "node_modules"
    
    if package_json.exists():
        print("   ✅ package.json encontrado")
        
        if node_modules.exists():
            print("   ✅ node_modules encontrado")
        else:
            print("   ⚠️  node_modules no encontrado")
            print("   💡 Ejecutar: cd frontend && npm install")
        
        return True
    else:
        print("   ❌ package.json no encontrado")
        return False

def generate_summary_report(tailscale_ip, checks_passed):
    """Genera un reporte resumen"""
    print("\n" + "=" * 80)
    print("📊 REPORTE DE VERIFICACIÓN")
    print("=" * 80)
    
    print(f"\n✅ Verificaciones exitosas: {sum(checks_passed)}/{len(checks_passed)}")
    
    if all(checks_passed):
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n🌐 Tu aplicación estará disponible en:")
        if tailscale_ip:
            print(f"   • Frontend: http://{tailscale_ip}:3000")
            print(f"   • Backend: https://{tailscale_ip}:8001")
            print(f"   • API Docs: https://{tailscale_ip}:8001/docs")
        
        print("\n🚀 Para iniciar la aplicación:")
        print("   1. Ejecuta: start_tailscale_secure.bat")
        print("   2. O ejecuta: python start_tailscale_secure.py")
        
        print("\n📱 Para acceder desde móvil:")
        print("   1. Instala Tailscale en tu dispositivo móvil")
        print("   2. Inicia sesión con la misma cuenta")
        print("   3. Usa las URLs mostradas arriba")
        
    else:
        print("\n⚠️  Algunas verificaciones fallaron")
        print("\nPor favor revisa los errores mostrados arriba y:")
        print("   1. Instala los componentes faltantes")
        print("   2. Configura Tailscale correctamente")
        print("   3. Ejecuta este script nuevamente")
    
    print("\n" + "=" * 80)

def main():
    """Función principal"""
    print_header()
    
    checks = [
        ("Tailscale instalado", check_tailscale_installation()),
        ("Tailscale conectado", check_tailscale_connection()),
        ("Python instalado", check_python_installation()),
        ("Node.js instalado", check_node_installation()),
        ("OpenSSL disponible", check_openssl_installation()),
        ("Archivos necesarios", check_required_files()),
        ("Dependencias backend", check_backend_dependencies()),
        ("Dependencias frontend", check_frontend_dependencies())
    ]
    
    tailscale_ip = get_tailscale_ip()
    checks_passed = [result for name, result in checks]
    
    generate_summary_report(tailscale_ip, checks_passed)
    
    return all(checks_passed)

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
