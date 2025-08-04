from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    category = Column(String, index=True)
    cover_image_url = Column(String, nullable=True)
    
    # Campos para Google Drive (almacenamiento principal)
    drive_file_id = Column(String, nullable=False) # ID del archivo en Google Drive (obligatorio)
    drive_web_link = Column(String, nullable=True) # Link web del archivo en Drive
    drive_letter_folder = Column(String, nullable=True) # Carpeta de letra (A-Z)
    drive_filename = Column(String, nullable=True) # Nombre original del archivo en Drive
    
    # Campo opcional para ruta local temporal (solo durante procesamiento)
    file_path = Column(String, nullable=True) # Ruta temporal local (opcional)
