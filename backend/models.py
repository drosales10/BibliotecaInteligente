from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    category = Column(String, index=True)
    cover_image_url = Column(String, nullable=True)
    file_path = Column(String, unique=True) # Ruta al archivo original (local)
    
    # Campos para Google Drive
    drive_file_id = Column(String, nullable=True) # ID del archivo en Google Drive
    drive_web_link = Column(String, nullable=True) # Link web del archivo en Drive
    drive_letter_folder = Column(String, nullable=True) # Carpeta de letra (A-Z)
    is_in_drive = Column(Boolean, default=False) # Indica si está en Google Drive
