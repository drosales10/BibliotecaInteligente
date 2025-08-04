import os
import io
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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

class GoogleDriveManager:
    """
    Gestor de Google Drive para almacenar libros organizados por categorías
    y orden alfabético A-Z
    """
    
    def __init__(self):
        self.service = None
        self.root_folder_id = None
        self.categories_cache = {}
        self.initialize_service()
    
    def initialize_service(self):
        """Inicializa el servicio de Google Drive"""
        try:
            creds = None
            
            # Cargar credenciales existentes
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Si no hay credenciales válidas, solicitar autorización
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(CREDENTIALS_FILE):
                        logger.error(f"Archivo {CREDENTIALS_FILE} no encontrado. Por favor, descárgalo desde Google Cloud Console.")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Guardar credenciales para la próxima ejecución
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            self.setup_root_folder()
            logger.info("Servicio de Google Drive inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar Google Drive: {e}")
    
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
            logger.error(f"Error al obtener/crear carpeta de categoría {category}: {e}")
            return None
    
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
            logger.error(f"Error al obtener/crear carpeta de letra para '{title}': {e}")
            return None
    
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
    
    def upload_book_to_drive(self, file_path, title, author, category):
        """Sube un libro a Google Drive con la organización especificada"""
        try:
            if not self.service:
                logger.error("Servicio de Google Drive no inicializado")
                return None
            
            # Obtener carpeta de categoría
            category_folder_id = self.get_or_create_category_folder(category)
            if not category_folder_id:
                return None
            
            # Obtener carpeta de letra
            letter_folder_id = self.get_letter_folder(category_folder_id, title)
            if not letter_folder_id:
                return None
            
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
            
            logger.info(f"Libro subido exitosamente: {title} (Drive ID: {file.get('id')})")
            return drive_file_info
            
        except Exception as e:
            logger.error(f"Error al subir libro {title} a Google Drive: {e}")
            return None
    
    def download_book_from_drive(self, file_id):
        """Descarga un libro desde Google Drive a un archivo temporal"""
        try:
            import tempfile
            
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
            
            # Crear archivo temporal con nombre único
            temp_filename = f"temp_download_{file_id}_{uuid.uuid4().hex[:8]}"
            temp_file_path = os.path.join(temp_dir, temp_filename)
            
            # Guardar archivo temporalmente
            with open(temp_file_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Libro descargado exitosamente: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error al descargar libro desde Google Drive: {e}")
            return None
    
    def delete_book_from_drive(self, file_id):
        """Elimina un libro de Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Libro eliminado de Google Drive: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar libro de Google Drive: {e}")
            return False
    
    def list_books_by_category(self, category):
        """Lista todos los libros de una categoría específica"""
        try:
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
            return []
    
    def get_storage_info(self):
        """Obtiene información sobre el uso de almacenamiento"""
        try:
            # Obtener información de la carpeta raíz
            folder = self.service.files().get(
                fileId=self.root_folder_id, 
                fields='id, name, size, quotaBytesUsed'
            ).execute()
            
            # Calcular tamaño total (aproximado)
            total_size = int(folder.get('quotaBytesUsed', 0))
            
            return {
                'root_folder_id': self.root_folder_id,
                'root_folder_name': folder.get('name'),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error al obtener información de almacenamiento: {e}")
            return None

# Instancia global del gestor
drive_manager = GoogleDriveManager() 