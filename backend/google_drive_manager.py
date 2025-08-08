import os
import io
import ssl
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import logging
from pathlib import Path
import json
import uuid
import time
import threading
from functools import wraps
import httplib2

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Google Drive API
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Configuración de caché y persistencia
CACHE_DURATION = 300  # 5 minutos
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos

def retry_on_error(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorador para reintentar operaciones en caso de error"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    # Manejo específico para errores SSL
                    if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper():
                        logger.warning(f"Error SSL detectado en {func.__name__}, intento {attempt + 1}/{max_retries}")
                        if attempt == 0:  # Solo en el primer intento, intentar reinicializar el servicio
                            try:
                                if hasattr(args[0], 'service') and args[0].service:
                                    logger.info("Reinicializando servicio de Google Drive debido a error SSL...")
                                    args[0].initialize_service()
                                    # Esperar un poco más después de reinicializar
                                    time.sleep(delay * 2)
                            except Exception as reinit_error:
                                logger.warning(f"Error al reinicializar servicio: {reinit_error}")
                    else:
                        logger.warning(f"Intento {attempt + 1}/{max_retries} falló para {func.__name__}: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Backoff exponencial
            logger.error(f"Todos los intentos fallaron para {func.__name__}: {last_exception}")
            raise last_exception
        return wrapper
    return decorator

class GoogleDriveManager:
    """
    Gestor de Google Drive para almacenar libros organizados por categorías
    y orden alfabético A-Z con sistema de caché y reconexión automática
    """
    
    def __init__(self):
        self.service = None
        self.root_folder_id = None
        self.categories_cache = {}
        self.storage_cache = None
        self.cache_timestamp = 0
        self._lock = threading.Lock()
        self.initialize_service()
    
    def _is_cache_valid(self):
        """Verifica si el caché es válido"""
        return (self.storage_cache is not None and 
                time.time() - self.cache_timestamp < CACHE_DURATION)
    
    def _clear_cache(self):
        """Limpia el caché"""
        with self._lock:
            self.storage_cache = None
            self.cache_timestamp = 0
            self.categories_cache.clear()
    
    def _ensure_service_connection(self):
        """Asegura que el servicio esté conectado, reintentando si es necesario"""
        if not self.service:
            logger.info("Servicio no inicializado, intentando reconectar...")
            self.initialize_service()
        
        if not self.service:
            raise Exception("No se pudo inicializar el servicio de Google Drive")
    
    @retry_on_error()
    def initialize_service(self):
        """Inicializa el servicio de Google Drive con manejo robusto de errores"""
        try:
            creds = None
            
            # Cargar credenciales existentes
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Si no hay credenciales válidas, solicitar autorización
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Credenciales refrescadas exitosamente")
                    except Exception as refresh_error:
                        logger.warning(f"Error al refrescar credenciales: {refresh_error}")
                        # Si falla el refresh, crear nuevas credenciales
                        creds = None
                
                if not creds:
                    if not os.path.exists(CREDENTIALS_FILE):
                        logger.error(f"Archivo {CREDENTIALS_FILE} no encontrado. Por favor, descárgalo desde Google Cloud Console.")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Guardar credenciales para la próxima ejecución
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            # Configurar SSL para evitar errores de versión
            try:
                # Intentar con configuración estándar primero
                self.service = build('drive', 'v3', credentials=creds)
            except Exception as ssl_error:
                if "WRONG_VERSION_NUMBER" in str(ssl_error) or "SSL" in str(ssl_error).upper():
                    logger.warning("Error SSL detectado, intentando con configuración alternativa...")
                    # Configuración alternativa para problemas SSL
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    # Crear contexto SSL personalizado
                    import ssl
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Configurar HTTP con contexto SSL personalizado
                    import httplib2
                    http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
                    self.service = build('drive', 'v3', credentials=creds, http=http)
                    
                    logger.info("Servicio de Google Drive inicializado con configuración SSL alternativa")
                else:
                    raise ssl_error
            
            self.setup_root_folder()
            logger.info("Servicio de Google Drive inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar Google Drive: {e}")
            self.service = None
            raise
    
    @retry_on_error()
    def setup_root_folder(self):
        """Configura la carpeta raíz para la biblioteca"""
        try:
            # Buscar carpeta raíz existente
            query = "name='Biblioteca Inteligente' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                self.root_folder_id = files[0]['id']
                logger.info(f"Carpeta raíz encontrada: {files[0]['name']} (ID: {self.root_folder_id})")
            else:
                # Crear carpeta raíz
                folder_metadata = {
                    'name': 'Biblioteca Inteligente',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.root_folder_id = folder.get('id')
                logger.info(f"Carpeta raíz creada: Biblioteca Inteligente (ID: {self.root_folder_id})")
                
        except Exception as e:
            logger.error(f"Error al configurar carpeta raíz: {e}")
            raise
    
    @retry_on_error()
    def get_or_create_category_folder(self, category):
        """Obtiene o crea una carpeta para una categoría específica"""
        try:
            if category in self.categories_cache:
                return self.categories_cache[category]
            
            # Buscar carpeta de categoría existente
            query = f"name='{category}' and mimeType='application/vnd.google-apps.folder' and '{self.root_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                self.categories_cache[category] = folder_id
                logger.info(f"Carpeta de categoría encontrada: {category} (ID: {folder_id})")
                return folder_id
            else:
                # Crear carpeta de categoría
                folder_metadata = {
                    'name': category,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.root_folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')
                self.categories_cache[category] = folder_id
                logger.info(f"Carpeta de categoría creada: {category} (ID: {folder_id})")
                return folder_id
                
        except Exception as e:
            error_msg = str(e)
            if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper() or "DECRYPTION_FAILED" in error_msg:
                logger.warning("Error SSL detectado en get_or_create_category_folder, intentando con configuración alternativa...")
                try:
                    # Recrear servicio con configuración SSL alternativa
                    from google.oauth2.credentials import Credentials
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    import urllib3
                    import ssl
                    import httplib2
                    
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
                    
                    if os.path.exists(TOKEN_FILE):
                        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                        creds = flow.run_local_server(port=0)
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(creds.to_json())
                    
                    self.service = build('drive', 'v3', credentials=creds, http=http)
                    
                    # Reintentar la operación
                    if category in self.categories_cache:
                        return self.categories_cache[category]
                    
                    query = f"name='{category}' and mimeType='application/vnd.google-apps.folder' and '{self.root_folder_id}' in parents and trashed=false"
                    results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                    files = results.get('files', [])
                    
                    if files:
                        folder_id = files[0]['id']
                        self.categories_cache[category] = folder_id
                        logger.info(f"✅ Carpeta de categoría encontrada con configuración SSL alternativa: {category} (ID: {folder_id})")
                        return folder_id
                    else:
                        folder_metadata = {
                            'name': category,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [self.root_folder_id]
                        }
                        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                        folder_id = folder.get('id')
                        self.categories_cache[category] = folder_id
                        logger.info(f"✅ Carpeta de categoría creada con configuración SSL alternativa: {category} (ID: {folder_id})")
                        return folder_id
                        
                except Exception as ssl_retry_error:
                    logger.error(f"❌ Error persistente SSL en get_or_create_category_folder: {ssl_retry_error}")
                    raise
            else:
                logger.error(f"Error al obtener/crear carpeta de categoría {category}: {e}")
                raise
    
    @retry_on_error()
    def get_letter_folder(self, category_folder_id, title):
        """Obtiene o crea una carpeta para la letra inicial del título"""
        try:
            # Obtener primera letra del título (ignorar artículos)
            first_letter = self.get_first_letter(title)
            
            # Buscar carpeta de letra existente
            query = f"name='{first_letter}' and mimeType='application/vnd.google-apps.folder' and '{category_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"Carpeta de letra encontrada: {first_letter} (ID: {folder_id})")
                return folder_id
            else:
                # Crear carpeta de letra
                folder_metadata = {
                    'name': first_letter,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [category_folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')
                logger.info(f"Carpeta de letra creada: {first_letter} (ID: {folder_id})")
                return folder_id
                
        except Exception as e:
            error_msg = str(e)
            if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper() or "DECRYPTION_FAILED" in error_msg:
                logger.warning("Error SSL detectado en get_letter_folder, intentando con configuración alternativa...")
                try:
                    # Recrear servicio con configuración SSL alternativa
                    from google.oauth2.credentials import Credentials
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    import urllib3
                    import ssl
                    import httplib2
                    
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
                    
                    if os.path.exists(TOKEN_FILE):
                        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                        creds = flow.run_local_server(port=0)
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(creds.to_json())
                    
                    self.service = build('drive', 'v3', credentials=creds, http=http)
                    
                    # Reintentar la operación
                    first_letter = self.get_first_letter(title)
                    query = f"name='{first_letter}' and mimeType='application/vnd.google-apps.folder' and '{category_folder_id}' in parents and trashed=false"
                    results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                    files = results.get('files', [])
                    
                    if files:
                        folder_id = files[0]['id']
                        logger.info(f"✅ Carpeta de letra encontrada con configuración SSL alternativa: {first_letter} (ID: {folder_id})")
                        return folder_id
                    else:
                        folder_metadata = {
                            'name': first_letter,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [category_folder_id]
                        }
                        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                        folder_id = folder.get('id')
                        logger.info(f"✅ Carpeta de letra creada con configuración SSL alternativa: {first_letter} (ID: {folder_id})")
                        return folder_id
                        
                except Exception as ssl_retry_error:
                    logger.error(f"❌ Error persistente SSL en get_letter_folder: {ssl_retry_error}")
                    raise
            else:
                logger.error(f"Error al obtener/crear carpeta de letra para '{title}': {e}")
                raise
    
    def get_first_letter(self, title):
        """Obtiene la primera letra significativa del título (ignorando artículos)"""
        # Artículos a ignorar
        articles = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'the', 'a', 'an']
        
        # Limpiar título y dividir en palabras
        words = title.lower().strip().split()
        
        # Buscar primera palabra que no sea artículo
        for word in words:
            if word not in articles:
                return word[0].upper()
        
        # Si todas son artículos, usar la primera letra del título
        return title[0].upper() if title else 'A'
    
    @retry_on_error()
    def upload_book_to_drive(self, file_path, title, author, category):
        """Sube un libro a Google Drive con la organización especificada"""
        try:
            self._ensure_service_connection()
            
            # Obtener carpeta de categoría
            category_folder_id = self.get_or_create_category_folder(category)
            if not category_folder_id:
                return {'success': False, 'error': 'No se pudo crear la carpeta de categoría'}
            
            # Obtener carpeta de letra
            letter_folder_id = self.get_letter_folder(category_folder_id, title)
            if not letter_folder_id:
                return {'success': False, 'error': 'No se pudo crear la carpeta de letra'}
            
            # Preparar metadatos del archivo
            filename = os.path.basename(file_path)
            file_metadata = {
                'name': filename,
                'parents': [letter_folder_id],
                'description': f'Título: {title}\nAutor: {author}\nCategoría: {category}'
            }
            
            # Subir archivo
            media = MediaIoBaseUpload(
                open(file_path, 'rb'),
                mimetype='application/pdf',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            drive_file_info = {
                'id': file.get('id'),
                'name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'category': category,
                'letter_folder': self.get_first_letter(title)
            }
            
            # Limpiar caché después de subir
            self._clear_cache()
            
            logger.info(f"Libro subido exitosamente: {title} (Drive ID: {file.get('id')})")
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_path': file.get('name'),
                'drive_info': drive_file_info
            }
            
        except Exception as e:
            error_msg = str(e)
            if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper() or "DECRYPTION_FAILED" in error_msg:
                logger.warning("Error SSL detectado en upload_book_to_drive, intentando con configuración alternativa...")
                try:
                    # Recrear servicio con configuración SSL alternativa
                    from google.oauth2.credentials import Credentials
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    import urllib3
                    import ssl
                    import httplib2
                    
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
                    
                    if os.path.exists(TOKEN_FILE):
                        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                        creds = flow.run_local_server(port=0)
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(creds.to_json())
                    
                    self.service = build('drive', 'v3', credentials=creds, http=http)
                    
                    # Reintentar toda la operación
                    self._ensure_service_connection()
                    
                    # Obtener carpeta de categoría
                    category_folder_id = self.get_or_create_category_folder(category)
                    if not category_folder_id:
                        return {'success': False, 'error': 'No se pudo crear la carpeta de categoría'}
                    
                    # Obtener carpeta de letra
                    letter_folder_id = self.get_letter_folder(category_folder_id, title)
                    if not letter_folder_id:
                        return {'success': False, 'error': 'No se pudo crear la carpeta de letra'}
                    
                    # Preparar metadatos del archivo
                    filename = os.path.basename(file_path)
                    file_metadata = {
                        'name': filename,
                        'parents': [letter_folder_id],
                        'description': f'Título: {title}\nAutor: {author}\nCategoría: {category}'
                    }
                    
                    # Subir archivo
                    media = MediaIoBaseUpload(
                        open(file_path, 'rb'),
                        mimetype='application/pdf',
                        resumable=True
                    )
                    
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, name, webViewLink'
                    ).execute()
                    
                    drive_file_info = {
                        'id': file.get('id'),
                        'name': file.get('name'),
                        'web_view_link': file.get('webViewLink'),
                        'category': category,
                        'letter_folder': self.get_first_letter(title)
                    }
                    
                    # Limpiar caché después de subir
                    self._clear_cache()
                    
                    logger.info(f"✅ Libro subido exitosamente con configuración SSL alternativa: {title} (Drive ID: {file.get('id')})")
                    return {
                        'success': True,
                        'file_id': file.get('id'),
                        'file_path': file.get('name'),
                        'drive_info': drive_file_info
                    }
                    
                except Exception as ssl_retry_error:
                    logger.error(f"❌ Error persistente SSL en upload_book_to_drive: {ssl_retry_error}")
                    return {'success': False, 'error': str(ssl_retry_error)}
            else:
                logger.error(f"Error al subir libro {title} a Google Drive: {e}")
                return {'success': False, 'error': str(e)}
    
    @retry_on_error()
    def download_book_from_drive(self, file_id):
        """Descarga un libro desde Google Drive a un archivo temporal"""
        try:
            import tempfile
            
            self._ensure_service_connection()
            
            # Obtener información del archivo para determinar la extensión
            file_info = self.service.files().get(fileId=file_id).execute()
            original_name = file_info.get('name', '')
            
            # Determinar la extensión basada en el nombre original o el tipo MIME
            mime_type = file_info.get('mimeType', '')
            if mime_type == 'application/pdf' or original_name.lower().endswith('.pdf'):
                extension = '.pdf'
            elif mime_type == 'application/epub+zip' or original_name.lower().endswith('.epub'):
                extension = '.epub'
            else:
                # Intentar extraer extensión del nombre original
                _, ext = os.path.splitext(original_name)
                extension = ext if ext else '.pdf'  # Por defecto PDF
            
            # Crear archivo temporal
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Descarga: {int(status.progress() * 100)}%")
            
            # Crear archivo temporal con nombre único y extensión correcta
            temp_filename = f"temp_download_{file_id}_{uuid.uuid4().hex[:8]}{extension}"
            temp_file_path = os.path.join(temp_dir, temp_filename)
            
            # Guardar archivo temporalmente
            with open(temp_file_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Libro descargado exitosamente: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error al descargar libro desde Google Drive: {e}")
            raise
    
    @retry_on_error()
    def delete_book_from_drive(self, file_id):
        """Elimina un libro de Google Drive"""
        try:
            self._ensure_service_connection()
            self.service.files().delete(fileId=file_id).execute()
            
            # Limpiar caché después de eliminar
            self._clear_cache()
            
            logger.info(f"Libro eliminado de Google Drive: {file_id}")
            return {'success': True, 'error': None}
            
        except Exception as e:
            logger.error(f"Error al eliminar libro de Google Drive: {e}")
            return {'success': False, 'error': str(e)}

    def delete_cover_from_drive(self, cover_url):
        """
        Elimina una imagen de portada de Google Drive basándose en su URL
        """
        try:
            self._ensure_service_connection()
            
            # Extraer el ID del archivo de la URL de Google Drive
            # Formato esperado: https://drive.google.com/file/d/{file_id}/view
            if 'drive.google.com/file/d/' in cover_url:
                file_id = cover_url.split('/file/d/')[1].split('/')[0]
                
                # Eliminar el archivo
                self.service.files().delete(fileId=file_id).execute()
                
                logger.info(f"Portada eliminada de Google Drive: {file_id}")
                return {'success': True, 'error': None}
            else:
                logger.warning(f"URL de portada no válida para eliminar: {cover_url}")
                return {'success': False, 'error': 'URL de portada no válida'}
                
        except Exception as e:
            logger.error(f"Error al eliminar portada de Google Drive: {e}")
            return {'success': False, 'error': str(e)}
    
    @retry_on_error()
    def list_books_by_category(self, category):
        """Lista todos los libros de una categoría específica"""
        try:
            self._ensure_service_connection()
            category_folder_id = self.get_or_create_category_folder(category)
            if not category_folder_id:
                return []
            
            # Buscar todos los archivos PDF en la categoría
            query = f"'{category_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name, description, createdTime)',
                orderBy='name'
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Encontrados {len(files)} libros en la categoría {category}")
            return files
            
        except Exception as e:
            logger.error(f"Error al listar libros de la categoría {category}: {e}")
            raise
    
    @retry_on_error()
    def list_all_books(self):
        """Lista todos los libros de todas las categorías"""
        try:
            self._ensure_service_connection()
            all_files = []
            
            # Obtener todas las carpetas de categorías
            category_query = f"'{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            category_results = self.service.files().list(
                q=category_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            category_folders = category_results.get('files', [])
            logger.info(f"Encontradas {len(category_folders)} carpetas de categorías")
            
            # Buscar archivos PDF en cada categoría y sus subcarpetas
            for category_folder in category_folders:
                category_id = category_folder['id']
                category_name = category_folder['name']
                
                # Obtener carpetas de letras en esta categoría
                letter_query = f"'{category_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
                letter_results = self.service.files().list(
                    q=letter_query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                letter_folders = letter_results.get('files', [])
                logger.info(f"Encontradas {len(letter_folders)} carpetas de letras en la categoría {category_name}")
                
                # Buscar archivos PDF en cada carpeta de letra
                for letter_folder in letter_folders:
                    letter_id = letter_folder['id']
                    letter_name = letter_folder['name']
                    
                    # Buscar archivos PDF en esta carpeta de letra
                    pdf_query = f"'{letter_id}' in parents and mimeType='application/pdf' and trashed=false"
                    pdf_results = self.service.files().list(
                        q=pdf_query,
                        spaces='drive',
                        fields='files(id, name, description, createdTime, parents)',
                        orderBy='name'
                    ).execute()
                    
                    letter_files = pdf_results.get('files', [])
                    all_files.extend(letter_files)
                    
                    if letter_files:
                        logger.info(f"Encontrados {len(letter_files)} libros en {category_name}/{letter_name}")
                
                # También buscar archivos PDF directamente en la categoría (por si acaso)
                direct_pdf_query = f"'{category_id}' in parents and mimeType='application/pdf' and trashed=false"
                direct_pdf_results = self.service.files().list(
                    q=direct_pdf_query,
                    spaces='drive',
                    fields='files(id, name, description, createdTime, parents)',
                    orderBy='name'
                ).execute()
                
                direct_files = direct_pdf_results.get('files', [])
                all_files.extend(direct_files)
                
                if direct_files:
                    logger.info(f"Encontrados {len(direct_files)} libros directamente en la categoría {category_name}")
            
            # También buscar archivos PDF directamente en la carpeta raíz
            root_pdf_query = f"'{self.root_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            root_pdf_results = self.service.files().list(
                q=root_pdf_query,
                spaces='drive',
                fields='files(id, name, description, createdTime, parents)',
                orderBy='name'
            ).execute()
            
            root_files = root_pdf_results.get('files', [])
            all_files.extend(root_files)
            
            if root_files:
                logger.info(f"Encontrados {len(root_files)} libros directamente en la carpeta raíz")
            
            logger.info(f"Total de libros encontrados: {len(all_files)}")
            return all_files
            
        except Exception as e:
            logger.error(f"Error al listar todos los libros: {e}")
            raise
    
    def get_storage_info(self):
        """Obtiene información sobre el uso de almacenamiento con caché"""
        try:
            # Verificar caché primero
            if self._is_cache_valid():
                logger.info("Retornando información de almacenamiento desde caché")
                return self.storage_cache
            
            self._ensure_service_connection()
            
            # Obtener información de la carpeta raíz
            folder = self.service.files().get(
                fileId=self.root_folder_id, 
                fields='id, name, size, quotaBytesUsed'
            ).execute()
            
            # Calcular tamaño total (aproximado)
            total_size = int(folder.get('quotaBytesUsed', 0))
            
            storage_info = {
                'root_folder_id': self.root_folder_id,
                'root_folder_name': folder.get('name'),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'cache_timestamp': time.time()
            }
            
            # Actualizar caché
            with self._lock:
                self.storage_cache = storage_info
                self.cache_timestamp = time.time()
            
            logger.info("Información de almacenamiento actualizada y cacheada")
            return storage_info
            
        except Exception as e:
            logger.error(f"Error al obtener información de almacenamiento: {e}")
            # Si hay error, limpiar caché y reintentar
            self._clear_cache()
            raise
    
    def health_check(self):
        """Verifica la salud de la conexión con Google Drive"""
        try:
            self._ensure_service_connection()
            
            # Intentar una operación simple
            test_query = f"'{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=test_query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            return {
                'status': 'healthy',
                'message': 'Conexión con Google Drive funcionando correctamente',
                'root_folder_id': self.root_folder_id,
                'test_successful': True
            }
            
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Error en la conexión: {str(e)}',
                'error_type': type(e).__name__,
                'test_successful': False
            }

    @retry_on_error()
    def upload_cover_image(self, file_path, title, author):
        """
        Sube una imagen de portada a Google Drive y devuelve la información del archivo
        """
        try:
            self._ensure_service_connection()
            
            # Crear carpeta para imágenes de portada si no existe
            covers_folder_id = self._get_or_create_covers_folder()
            if not covers_folder_id:
                logger.error("❌ No se pudo crear la carpeta de portadas")
                return None
            
            # Generar nombre único para la imagen
            file_extension = Path(file_path).suffix.lower()
            timestamp = int(time.time())
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"cover_{safe_title}_{safe_author}_{timestamp}{file_extension}"
            
            # Leer el archivo de imagen
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Crear metadata del archivo
            file_metadata = {
                'name': filename,
                'parents': [covers_folder_id],
                'description': f'Portada del libro "{title}" de {author}'
            }
            
            # Crear media para la subida
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype='image/png' if file_extension == '.png' else 'image/jpeg',
                resumable=True
            )
            
            # Subir archivo
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink,size'
            ).execute()
            
            logger.info(f"✅ Imagen de portada subida: {filename} (ID: {file.get('id')})")
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink'),
                'size': file.get('size')
            }
            
        except Exception as e:
            error_msg = str(e)
            if "WRONG_VERSION_NUMBER" in error_msg or "SSL" in error_msg.upper():
                logger.warning("Error SSL detectado en upload_cover_image, intentando con configuración alternativa...")
                try:
                    # Recrear el servicio con configuración SSL alternativa
                    from google.oauth2.credentials import Credentials
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    import urllib3
                    import ssl
                    import httplib2
                    
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    # Crear contexto SSL personalizado
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Configurar HTTP con contexto SSL personalizado
                    http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
                    
                    # Recrear credenciales y servicio
                    if os.path.exists(TOKEN_FILE):
                        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                        creds = flow.run_local_server(port=0)
                        with open(TOKEN_FILE, 'w') as token:
                            token.write(creds.to_json())
                    
                    # Recrear servicio con configuración SSL alternativa
                    self.service = build('drive', 'v3', credentials=creds, http=http)
                    
                    # Reintentar la operación completa
                    covers_folder_id = self._get_or_create_covers_folder()
                    if not covers_folder_id:
                        logger.error("❌ No se pudo crear la carpeta de portadas con configuración SSL alternativa")
                        return None
                    
                    # Generar nombre único para la imagen
                    file_extension = Path(file_path).suffix.lower()
                    timestamp = int(time.time())
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"cover_{safe_title}_{safe_author}_{timestamp}{file_extension}"
                    
                    # Leer el archivo de imagen
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Crear metadata del archivo
                    file_metadata = {
                        'name': filename,
                        'parents': [covers_folder_id],
                        'description': f'Portada del libro "{title}" de {author}'
                    }
                    
                    # Crear media para la subida
                    media = MediaIoBaseUpload(
                        io.BytesIO(file_content),
                        mimetype='image/png' if file_extension == '.png' else 'image/jpeg',
                        resumable=True
                    )
                    
                    # Subir archivo
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id,name,webViewLink,webContentLink,size'
                    ).execute()
                    
                    logger.info(f"✅ Imagen de portada subida con configuración SSL alternativa: {filename} (ID: {file.get('id')})")
                    
                    return {
                        'id': file.get('id'),
                        'name': file.get('name'),
                        'web_view_link': file.get('webViewLink'),
                        'web_content_link': file.get('webContentLink'),
                        'size': file.get('size')
                    }
                    
                except Exception as ssl_retry_error:
                    logger.error(f"❌ Error persistente SSL en upload_cover_image: {ssl_retry_error}")
                    return None
            else:
                logger.error(f"❌ Error al subir imagen de portada: {e}")
                return None
    
    @retry_on_error()
    def _get_or_create_covers_folder(self):
        """
        Obtiene o crea la carpeta para imágenes de portada
        """
        try:
            # Buscar carpeta de portadas en la raíz
            query = f"name='Portadas' and '{self.root_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id,name)').execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            # Crear carpeta si no existe
            folder_metadata = {
                'name': 'Portadas',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.root_folder_id],
                'description': 'Carpeta para imágenes de portada de libros'
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name'
            ).execute()
            
            logger.info(f"✅ Carpeta de portadas creada: {folder.get('name')} (ID: {folder.get('id')})")
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"❌ Error al obtener/crear carpeta de portadas: {e}")
            return None

    def extract_folder_id_from_url(self, drive_url):
        """
        Extrae el ID de carpeta de una URL pública de Google Drive
        """
        try:
            # Patrones comunes de URLs de Google Drive
            patterns = [
                r'drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)',
                r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
                r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
                r'id=([a-zA-Z0-9_-]+)'
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, drive_url)
                if match:
                    folder_id = match.group(1)
                    logger.info(f"✅ ID de carpeta extraído: {folder_id}")
                    return folder_id
            
            logger.error(f"❌ No se pudo extraer ID de carpeta de la URL: {drive_url}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error al extraer ID de carpeta: {e}")
            return None

    @retry_on_error()
    def list_public_folder_contents(self, folder_url):
        """
        Lista el contenido de una carpeta pública de Google Drive (incluyendo carpetas de otros usuarios)
        """
        try:
            folder_id = self.extract_folder_id_from_url(folder_url)
            if not folder_id:
                return {"success": False, "error": "No se pudo extraer el ID de carpeta de la URL"}
            
            # Obtener información de la carpeta
            try:
                folder_info = self.service.files().get(
                    fileId=folder_id,
                    fields='id,name,mimeType,webViewLink,owners'
                ).execute()
                
                if folder_info.get('mimeType') != 'application/vnd.google-apps.folder':
                    return {"success": False, "error": "La URL no corresponde a una carpeta de Google Drive"}
                
                # Verificar si la carpeta es accesible (pública o compartida)
                owners = folder_info.get('owners', [])
                if owners:
                    owner_email = owners[0].get('emailAddress', '')
                    print(f"📁 Carpeta de usuario: {owner_email}")
                
            except HttpError as e:
                if e.resp.status == 404:
                    return {"success": False, "error": "La carpeta no existe o no es accesible"}
                elif e.resp.status == 403:
                    return {"success": False, "error": "No tienes permisos para acceder a esta carpeta. Verifica que sea pública."}
                else:
                    raise e
            
            # Listar contenido de la carpeta
            files = []
            page_token = None
            
            while True:
                try:
                    results = self.service.files().list(
                        q=f"'{folder_id}' in parents and trashed=false",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, size, webViewLink, webContentLink, owners)',
                        pageToken=page_token
                    ).execute()
                    
                    items = results.get('files', [])
                    files.extend(items)
                    
                    page_token = results.get('nextPageToken', None)
                    if page_token is None:
                        break
                        
                except HttpError as e:
                    if e.resp.status == 403:
                        logger.error(f"❌ Error de permisos al listar contenido: {e}")
                        return {"success": False, "error": "No tienes permisos para listar el contenido de esta carpeta. Verifica que sea pública."}
                    else:
                        logger.error(f"❌ Error al listar contenido de carpeta: {e}")
                        break
            
            logger.info(f"✅ Contenido de carpeta listado: {len(files)} elementos encontrados")
            return {
                "success": True,
                "folder_info": folder_info,
                "files": files,
                "total_files": len(files)
            }
            
        except Exception as e:
            logger.error(f"❌ Error al listar carpeta pública: {e}")
            return {"success": False, "error": f"Error al listar carpeta: {str(e)}"}

    @retry_on_error()
    def download_file_from_drive(self, file_id, temp_dir):
        """
        Descarga un archivo desde Google Drive a un directorio temporal
        """
        try:
            # Obtener información del archivo
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size'
            ).execute()
            
            file_name = file_info.get('name', 'unknown_file')
            file_size = int(file_info.get('size', 0))
            
            # Crear ruta temporal
            temp_file_path = os.path.join(temp_dir, file_name)
            
            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)
            
            with open(temp_file_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Descargando {file_name}: {int(status.progress() * 100)}%")
            
            logger.info(f"✅ Archivo descargado: {file_name} ({file_size} bytes)")
            return {
                "success": True,
                "file_path": temp_file_path,
                "file_name": file_name,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"❌ Error al descargar archivo {file_id}: {e}")
            return {"success": False, "error": str(e)}

    def process_public_folder_recursively(self, folder_url, temp_dir):
        """
        Procesa recursivamente una carpeta pública de Google Drive (incluyendo carpetas de otros usuarios)
        """
        try:
            # Listar contenido de la carpeta
            folder_result = self.list_public_folder_contents(folder_url)
            if not folder_result["success"]:
                return folder_result
            
            all_files = []
            processed_folders = set()
            
            def process_folder_recursive(folder_id, folder_name="", depth=0):
                """Función recursiva para procesar carpetas"""
                if folder_id in processed_folders:
                    return
                
                processed_folders.add(folder_id)
                indent = "  " * depth
                logger.info(f"{indent}📁 Procesando carpeta: {folder_name}")
                
                # Listar contenido de la carpeta
                page_token = None
                while True:
                    try:
                        results = self.service.files().list(
                            q=f"'{folder_id}' in parents and trashed=false",
                            spaces='drive',
                            fields='nextPageToken, files(id, name, mimeType, size, webViewLink, owners)',
                            pageToken=page_token
                        ).execute()
                        
                        items = results.get('files', [])
                        
                        for item in items:
                            item_name = item.get('name', '')
                            item_id = item.get('id')
                            mime_type = item.get('mimeType', '')
                            
                            if mime_type == 'application/vnd.google-apps.folder':
                                # Es una subcarpeta, procesar recursivamente
                                logger.info(f"{indent}📁 Subcarpeta encontrada: {item_name}")
                                try:
                                    process_folder_recursive(item_id, item_name, depth + 1)
                                except Exception as e:
                                    logger.warning(f"{indent}⚠️ No se pudo acceder a subcarpeta {item_name}: {e}")
                            else:
                                # Es un archivo, verificar si es un libro
                                if self.is_valid_book_file(item_name):
                                    logger.info(f"{indent}📄 Libro encontrado: {item_name}")
                                    all_files.append({
                                        "id": item_id,
                                        "name": item_name,
                                        "size": item.get('size', 0),
                                        "web_link": item.get('webViewLink'),
                                        "folder_path": folder_name
                                    })
                                else:
                                    logger.info(f"{indent}❌ Archivo ignorado: {item_name}")
                        
                        page_token = results.get('nextPageToken', None)
                        if page_token is None:
                            break
                            
                    except HttpError as e:
                        if e.resp.status == 403:
                            logger.warning(f"{indent}⚠️ No se pudo acceder al contenido de {folder_name}: Permisos insuficientes")
                            break
                        else:
                            logger.error(f"{indent}❌ Error al listar contenido: {e}")
                            break
            
            # Procesar la carpeta raíz
            folder_id = self.extract_folder_id_from_url(folder_url)
            folder_info = folder_result["folder_info"]
            process_folder_recursive(folder_id, folder_info.get('name', 'Carpeta raíz'))
            
            logger.info(f"✅ Procesamiento recursivo completado: {len(all_files)} libros encontrados")
            return {
                "success": True,
                "folder_info": folder_info,
                "books": all_files,
                "total_books": len(all_files)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento recursivo: {e}")
            return {"success": False, "error": f"Error en procesamiento: {str(e)}"}

    def is_valid_book_file(self, filename):
        """
        Verifica si un archivo es un libro válido (PDF o EPUB)
        """
        valid_extensions = {'.pdf', '.epub'}
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in valid_extensions

    def check_folder_accessibility(self, folder_url):
        """
        Verifica si una carpeta es accesible públicamente
        """
        try:
            folder_id = self.extract_folder_id_from_url(folder_url)
            if not folder_id:
                return {"success": False, "error": "No se pudo extraer el ID de carpeta de la URL"}
            
            # Intentar obtener información básica de la carpeta
            try:
                folder_info = self.service.files().get(
                    fileId=folder_id,
                    fields='id,name,mimeType,webViewLink,owners,permissions'
                ).execute()
                
                if folder_info.get('mimeType') != 'application/vnd.google-apps.folder':
                    return {"success": False, "error": "La URL no corresponde a una carpeta de Google Drive"}
                
                # Verificar propietario
                owners = folder_info.get('owners', [])
                owner_email = owners[0].get('emailAddress', '') if owners else 'Desconocido'
                
                # Verificar permisos
                permissions = folder_info.get('permissions', [])
                is_public = any(perm.get('type') == 'anyone' for perm in permissions)
                
                return {
                    "success": True,
                    "folder_info": folder_info,
                    "owner": owner_email,
                    "is_public": is_public,
                    "accessible": True
                }
                
            except HttpError as e:
                if e.resp.status == 404:
                    return {"success": False, "error": "La carpeta no existe"}
                elif e.resp.status == 403:
                    return {"success": False, "error": "La carpeta no es accesible públicamente. Verifica que esté compartida como pública."}
                else:
                    return {"success": False, "error": f"Error al acceder a la carpeta: {e}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Error al verificar accesibilidad: {str(e)}"}

# Instancia global del gestor
drive_manager = None

def get_drive_manager():
    """Obtiene la instancia global del gestor de Google Drive, inicializándola si es necesario"""
    global drive_manager
    if drive_manager is None:
        try:
            drive_manager = GoogleDriveManager()
        except Exception as e:
            logger.error(f"Error al inicializar Google Drive Manager: {e}")
            raise
    return drive_manager 