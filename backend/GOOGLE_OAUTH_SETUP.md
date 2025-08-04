# Configuración de Google OAuth

Para usar la funcionalidad de Google Drive en esta aplicación, necesitas configurar la autenticación OAuth.

## Pasos para configurar:

1. **Crear un proyecto en Google Cloud Console**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un nuevo proyecto o selecciona uno existente
   - Habilita la API de Google Drive

2. **Configurar credenciales OAuth**
   - Ve a "APIs & Services" > "Credentials"
   - Haz clic en "Create Credentials" > "OAuth 2.0 Client IDs"
   - Selecciona "Desktop application"
   - Descarga el archivo JSON de credenciales

3. **Configurar los archivos**
   - Copia el archivo descargado como `credentials.json` en la carpeta `backend/`
   - Ejecuta el script de configuración: `python setup_google_drive.py`
   - Esto generará automáticamente el archivo `token.json`

## Archivos necesarios:

- `credentials.json` - Contiene las credenciales de tu aplicación (NO subir al repositorio)
- `token.json` - Contiene los tokens de acceso (NO subir al repositorio)

## Archivos de ejemplo:

- `credentials_template.json` - Plantilla para `credentials.json`
- `token_template.json` - Plantilla para `token.json`

## Seguridad:

⚠️ **IMPORTANTE**: Nunca subas los archivos `credentials.json` o `token.json` al repositorio, ya que contienen información sensible. Estos archivos ya están incluidos en `.gitignore`. 