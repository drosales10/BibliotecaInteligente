#!/usr/bin/env python3
"""
Script maestro para iniciar Biblioteca Inteligente de manera segura con Tailscale
Inicia tanto el backend como el frontend con configuración optimizada para acceso móvil
"""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path

# Importar configuración de Tailscale
from tailscale_config import get_secure_config_for_tailscale, ensure_tailscale_connection

def print_banner():
    """
    Muestra el banner de inicio
    """
    print("=" * 80)
    print("🌐 BIBLIOTECA INTELIGENTE - MODO SEGURO CON TAILSCALE")
    print("=" * 80)
    print("📱 Acceso seguro desde dispositivos móviles")
    print("🔒 Conexión cifrada a través de red privada Tailscale")
    print("=" * 80)

def run_backend():
    """
    Ejecuta el backend en un hilo separado
    """
    try:
        print("🚀 Iniciando backend...")
        result = subprocess.run([
            sys.executable, "start_tailscale_backend.py"
        ], check=False)
        
        if result.returncode != 0:
            print("❌ Backend terminó con error")
        else:
            print("✅ Backend terminado correctamente")
            
    except Exception as e:
        print(f"❌ Error en backend: {e}")

def run_frontend():
    """
    Ejecuta el frontend en un hilo separado
    """
    try:
        # Esperar un poco para que el backend se inicie primero
        time.sleep(5)
        
        print("🚀 Iniciando frontend...")
        result = subprocess.run([
            sys.executable, "start_tailscale_frontend.py"
        ], check=False)
        
        if result.returncode != 0:
            print("❌ Frontend terminó con error")
        else:
            print("✅ Frontend terminado correctamente")
            
    except Exception as e:
        print(f"❌ Error en frontend: {e}")

def main():
    """
    Función principal que coordina el inicio de ambos servicios
    """
    print_banner()
    
    # Verificar conexión de Tailscale
    if not ensure_tailscale_connection():
        print("\n❌ No se puede continuar sin una conexión Tailscale activa")
        print("\n💡 Para configurar Tailscale:")
        print("   1. Abre la aplicación de Tailscale desde el menú de inicio")
        print("   2. Inicia sesión con tu cuenta")
        print("   3. Asegúrate de que aparezca como 'Conectado'")
        print("   4. Vuelve a ejecutar este script")
        
        input("\n📱 Presiona Enter cuando Tailscale esté conectado...")
        return
    
    # Obtener configuración
    config = get_secure_config_for_tailscale()
    if not config:
        print("❌ No se pudo obtener configuración de Tailscale")
        return
    
    tailscale_ip = config['host']
    backend_port = config['port']
    frontend_port = config['frontend_port']
    use_ssl = config['use_ssl']
    protocol = "https" if use_ssl else "http"
    
    print(f"\n✅ Configuración de Tailscale detectada:")
    print(f"   🌐 IP: {tailscale_ip}")
    print(f"   🔗 Backend: {protocol}://{tailscale_ip}:{backend_port}")
    print(f"   🖥️  Frontend: http://{tailscale_ip}:{frontend_port}")
    print(f"   🔒 SSL: {'Habilitado' if use_ssl else 'Deshabilitado'}")
    
    print(f"\n📱 URLs para dispositivos móviles:")
    print(f"   Aplicación: http://{tailscale_ip}:{frontend_port}")
    print(f"   API: {protocol}://{tailscale_ip}:{backend_port}/docs")
    
    print(f"\n⚠️  IMPORTANTE:")
    print(f"   • Estas URLs solo funcionan en dispositivos conectados a tu Tailscale")
    print(f"   • Instala la app Tailscale en tu móvil e inicia sesión con la misma cuenta")
    print(f"   • Una vez conectado, podrás acceder desde cualquier lugar")
    
    input(f"\n🚀 Presiona Enter para iniciar ambos servicios...")
    
    try:
        # Crear hilos para backend y frontend
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        frontend_thread = threading.Thread(target=run_frontend, daemon=True)
        
        # Iniciar hilos
        backend_thread.start()
        frontend_thread.start()
        
        print(f"\n🔄 Servicios iniciándose...")
        print(f"⏳ Espera unos segundos para que se inicialicen completamente")
        print(f"⏹️  Presiona Ctrl+C para detener ambos servicios")
        
        # Esperar a que terminen los hilos
        while backend_thread.is_alive() or frontend_thread.is_alive():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Deteniendo servicios...")
        print(f"✅ Ambos servicios han sido detenidos")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando servicios: {e}")

if __name__ == "__main__":
    main()
