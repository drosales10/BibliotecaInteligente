import requests
import os
import time
import logging
from typing import Optional, Dict, List
from urllib.parse import quote_plus
import json
from PIL import Image
import io

logger = logging.getLogger(__name__)

class CoverSearchEngine:
    """
    Motor de búsqueda de portadas de libros en internet
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_google_images(self, title: str, author: str = None) -> Optional[str]:
        """
        Busca portadas usando Google Images
        """
        try:
            # Construir query de búsqueda
            query = f'"{title}"'
            if author:
                query += f' "{author}"'
            query += ' portada libro cover'
            
            # URL de búsqueda de Google Images
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&tbs=isz:l"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Extraer URLs de imágenes del HTML (método básico)
            content = response.text
            image_urls = []
            
            # Buscar URLs de imágenes en el contenido
            import re
            # Patrón para encontrar URLs de imágenes de Google
            pattern = r'https://[^"]*\.(?:jpg|jpeg|png|webp)[^"]*'
            matches = re.findall(pattern, content)
            
            for url in matches[:5]:  # Tomar las primeras 5 imágenes
                if 'gstatic.com' in url or 'googleusercontent.com' in url:
                    # Limpiar URL
                    clean_url = url.split('\\')[0] if '\\' in url else url
                    image_urls.append(clean_url)
            
            if image_urls:
                return image_urls[0]  # Retornar la primera imagen encontrada
                
        except Exception as e:
            logger.warning(f"Error en búsqueda de Google Images: {e}")
        
        return None
    
    def search_openlibrary(self, title: str, author: str = None) -> Optional[str]:
        """
        Busca portadas usando la API de OpenLibrary
        """
        try:
            # Construir query para OpenLibrary
            query = title
            if author:
                query += f" {author}"
            
            # Buscar libros en OpenLibrary
            search_url = f"https://openlibrary.org/search.json?q={quote_plus(query)}&limit=5"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get('docs', [])
            
            for doc in docs:
                # Buscar cover_i (ID de portada)
                cover_id = doc.get('cover_i')
                if cover_id:
                    # Construir URL de la portada
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                    return cover_url
                
                # Alternativa: buscar cover_edition_key
                edition_key = doc.get('cover_edition_key')
                if edition_key:
                    cover_url = f"https://covers.openlibrary.org/b/olid/{edition_key}-L.jpg"
                    return cover_url
                    
        except Exception as e:
            logger.warning(f"Error en búsqueda de OpenLibrary: {e}")
        
        return None
    
    def search_goodreads(self, title: str, author: str = None) -> Optional[str]:
        """
        Busca portadas usando Goodreads (simulado)
        """
        try:
            # Construir query
            query = f'"{title}"'
            if author:
                query += f' "{author}"'
            query += ' goodreads portada'
            
            # Usar Google Images para buscar en Goodreads
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&tbs=site:goodreads.com"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            import re
            pattern = r'https://[^"]*\.(?:jpg|jpeg|png|webp)[^"]*'
            matches = re.findall(pattern, content)
            
            for url in matches[:3]:
                if 'goodreads.com' in url:
                    clean_url = url.split('\\')[0] if '\\' in url else url
                    return clean_url
                    
        except Exception as e:
            logger.warning(f"Error en búsqueda de Goodreads: {e}")
        
        return None
    
    def search_amazon(self, title: str, author: str = None) -> Optional[str]:
        """
        Busca portadas usando Amazon (simulado)
        """
        try:
            # Construir query
            query = f'"{title}"'
            if author:
                query += f' "{author}"'
            query += ' amazon portada libro'
            
            # Usar Google Images para buscar en Amazon
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&tbs=site:amazon.com"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            import re
            pattern = r'https://[^"]*\.(?:jpg|jpeg|png|webp)[^"]*'
            matches = re.findall(pattern, content)
            
            for url in matches[:3]:
                if 'amazon.com' in url and ('images' in url or 'media' in url):
                    clean_url = url.split('\\')[0] if '\\' in url else url
                    return clean_url
                    
        except Exception as e:
            logger.warning(f"Error en búsqueda de Amazon: {e}")
        
        return None
    
    def download_and_validate_image(self, image_url: str, static_dir: str, title: str, author: str = None) -> Optional[str]:
        """
        Descarga y valida una imagen de portada
        """
        try:
            # Descargar imagen
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            
            # Verificar que es una imagen válida
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL no es una imagen válida: {content_type}")
                return None
            
            # Cargar imagen con PIL para validar
            try:
                img = Image.open(io.BytesIO(response.content))
                
                # Verificar dimensiones mínimas
                if img.width < 200 or img.height < 200:
                    logger.warning(f"Imagen demasiado pequeña: {img.width}x{img.height}")
                    return None
                
                # Verificar proporción (debe ser aproximadamente rectangular)
                ratio = img.width / img.height
                if ratio < 0.5 or ratio > 2.0:
                    logger.warning(f"Proporción de imagen inusual: {ratio}")
                    return None
                
                # Generar nombre de archivo
                base_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                base_name = base_name.replace(' ', '_')
                if author:
                    author_name = "".join(c for c in author if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    author_name = author_name.replace(' ', '_')
                    base_name += f"_{author_name}"
                
                timestamp = int(time.time())
                cover_filename = f"cover_online_{base_name}_{timestamp}.jpg"
                cover_full_path = os.path.join(static_dir, cover_filename)
                
                # Guardar imagen
                img.save(cover_full_path, 'JPEG', quality=85)
                
                # Verificar que se guardó correctamente
                if os.path.exists(cover_full_path):
                    file_size = os.path.getsize(cover_full_path)
                    logger.info(f"✅ Portada online descargada: {cover_filename} ({file_size} bytes)")
                    return cover_filename
                else:
                    logger.error(f"❌ Error al guardar portada online: {cover_full_path}")
                    return None
                    
            except Exception as e:
                logger.warning(f"Error al procesar imagen: {e}")
                return None
                
        except Exception as e:
            logger.warning(f"Error al descargar imagen: {e}")
            return None
    
    def search_book_cover(self, title: str, author: str = None, static_dir: str = "static/covers") -> Optional[str]:
        """
        Busca una portada de libro usando múltiples fuentes
        """
        logger.info(f"🔍 Buscando portada online para: '{title}' por '{author}'")
        
        # Crear directorio si no existe
        os.makedirs(static_dir, exist_ok=True)
        
        # Lista de métodos de búsqueda en orden de preferencia
        search_methods = [
            ("OpenLibrary", lambda: self.search_openlibrary(title, author)),
            ("Google Images", lambda: self.search_google_images(title, author)),
            ("Goodreads", lambda: self.search_goodreads(title, author)),
            ("Amazon", lambda: self.search_amazon(title, author))
        ]
        
        for method_name, search_func in search_methods:
            try:
                logger.info(f"🔍 Intentando búsqueda en {method_name}...")
                image_url = search_func()
                
                if image_url:
                    logger.info(f"✅ URL encontrada en {method_name}: {image_url}")
                    
                    # Descargar y validar imagen
                    cover_filename = self.download_and_validate_image(image_url, static_dir, title, author)
                    if cover_filename:
                        logger.info(f"✅ Portada online obtenida exitosamente: {cover_filename}")
                        return cover_filename
                    else:
                        logger.warning(f"⚠️ Imagen de {method_name} no pudo ser descargada o validada")
                else:
                    logger.info(f"❌ No se encontraron resultados en {method_name}")
                    
            except Exception as e:
                logger.warning(f"❌ Error en búsqueda de {method_name}: {e}")
                continue
            
            # Pausa entre búsquedas para evitar rate limiting
            time.sleep(1)
        
        logger.warning(f"❌ No se pudo encontrar portada online para: '{title}'")
        return None

# Instancia global del motor de búsqueda
cover_search_engine = CoverSearchEngine()

def search_book_cover_online(title: str, author: str = None, static_dir: str = "static/covers") -> Optional[str]:
    """
    Función de conveniencia para buscar portadas online
    """
    return cover_search_engine.search_book_cover(title, author, static_dir)
