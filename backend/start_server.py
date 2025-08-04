import uvicorn
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Iniciando servidor de la librería inteligente...")
    print("Puerto: 8001")
    print("Host: localhost")
    print("Presiona Ctrl+C para detener el servidor")
    
    try:
        uvicorn.run(
            "main:app",
            host="localhost",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        sys.exit(1) 