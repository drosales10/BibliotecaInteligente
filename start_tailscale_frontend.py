#!/usr/bin/env python3
"""
Script para iniciar el frontend de Biblioteca Inteligente con configuración para Tailscale
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Importar configuración de Tailscale
from tailscale_config import get_secure_config_for_tailscale

def update_frontend_proxy_config(tailscale_ip, backend_port, use_ssl=True):
    """
    Actualiza la configuración del proxy del frontend para usar Tailscale
    """
    frontend_dir = Path(__file__).parent / "frontend"
    proxy_file = frontend_dir / "setupProxy.js"
    
    protocol = "https" if use_ssl else "http"
    backend_url = f"{protocol}://{tailscale_ip}:{backend_port}"
    
    proxy_content = f'''const {{ createProxyMiddleware }} = require('http-proxy-middleware');

module.exports = function(app) {{
  console.log('🔧 Configurando proxy para Tailscale...');
  console.log('🌐 Backend URL:', '{backend_url}');
  
  app.use(
    '/api',
    createProxyMiddleware({{
      target: '{backend_url}',
      changeOrigin: true,
      secure: false, // Permitir certificados autofirmados
      logLevel: 'debug',
      headers: {{
        'X-Forwarded-Proto': '{protocol}',
        'X-Forwarded-Host': '{tailscale_ip}',
      }},
      onError: (err, req, res) => {{
        console.error('❌ Error en proxy API:', err);
        console.error('   Request URL:', req.url);
        console.error('   Request method:', req.method);
        console.error('   Backend URL:', '{backend_url}');
      }},
      onProxyReq: (proxyReq, req, res) => {{
        console.log('🔍 Proxy request:', req.method, req.url);
        console.log('🔍 Target URL:', proxyReq.path);
        console.log('🔍 Target host:', proxyReq.getHeader('host'));
      }},
      onProxyRes: (proxyRes, req, res) => {{
        console.log('✅ Proxy response:', proxyRes.statusCode, req.url);
        console.log('🔍 Content-Type:', proxyRes.headers['content-type']);
      }}
    }})
  );
  
  console.log('✅ Proxy configurado para /api -> {backend_url}');
}};'''
    
    try:
        with open(proxy_file, 'w', encoding='utf-8') as f:
            f.write(proxy_content)
        
        print(f"✅ Configuración del proxy actualizada")
        print(f"🔗 Frontend -> Backend: {backend_url}")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando configuración del proxy: {e}")
        return False

def start_secure_frontend():
    """
    Inicia el frontend con configuración para Tailscale
    """
    print("🚀 Iniciando Biblioteca Inteligente - Frontend para Tailscale")
    print("=" * 70)
    
    # Obtener configuración de Tailscale
    config = get_secure_config_for_tailscale()
    if not config:
        print("❌ No se pudo obtener configuración de Tailscale")
        print("💡 Asegúrate de que Tailscale esté instalado y conectado")
        return False
    
    tailscale_ip = config['host']
    backend_port = config['port']
    frontend_port = config['frontend_port']
    use_ssl = config['use_ssl']
    
    print(f"🌐 IP de Tailscale: {tailscale_ip}")
    print(f"🔌 Puerto Frontend: {frontend_port}")
    print(f"🔗 Puerto Backend: {backend_port}")
    print(f"🔒 SSL Backend: {'Habilitado' if use_ssl else 'Deshabilitado'}")
    
    # Actualizar configuración del proxy
    if not update_frontend_proxy_config(tailscale_ip, backend_port, use_ssl):
        return False
    
    # Cambiar al directorio del frontend
    frontend_dir = Path(__file__).parent / "frontend"
    
    print(f"📁 Cambiando al directorio: {frontend_dir}")
    os.chdir(frontend_dir)
    
    print(f"\n🔧 Instalando dependencias del frontend...")
    
    # Verificar si node_modules existe
    if not (frontend_dir / "node_modules").exists():
        print("📦 Instalando dependencias de Node.js...")
        try:
            subprocess.run(["npm", "install"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    
    # Verificar si existe el build
    build_dir = frontend_dir / "build"
    if not build_dir.exists():
        print("🏗️  Construyendo aplicación...")
        try:
            subprocess.run(["npm", "run", "build"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error construyendo aplicación: {e}")
            return False
    
    print(f"\n✅ Configuración completada")
    print(f"🌐 URL del frontend: http://{tailscale_ip}:{frontend_port}")
    print(f"📱 Accesible desde cualquier dispositivo en tu red Tailscale")
    print(f"⏹️  Presiona Ctrl+C para detener el servidor")
    print("-" * 70)
    
    # Configurar variables de entorno para el frontend
    env = os.environ.copy()
    env['HOST'] = tailscale_ip
    env['PORT'] = str(frontend_port)
    
    try:
        # Iniciar el servidor del frontend usando npm run serve
        print(f"🚀 Iniciando servidor con npm run serve...")
        print(f"📁 Directorio actual: {os.getcwd()}")
        
        # Intentar con npm directamente
        try:
            subprocess.run([
                "npm", "run", "serve"
            ], env=env, check=True, shell=True)
        except FileNotFoundError:
            # Intentar con cmd /c npm como respaldo
            print("Intentando con cmd /c npm...")
            subprocess.run([
                "cmd", "/c", "npm", "run", "serve"
            ], env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  Servidor frontend detenido por el usuario")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al iniciar el servidor frontend: {e}")
        print("💡 Verifica que:")
        print("   - Node.js esté instalado")
        print("   - Las dependencias estén instaladas (npm install)")
        print("   - El puerto no esté en uso")
        return False

if __name__ == "__main__":
    success = start_secure_frontend()
    if not success:
        sys.exit(1)
