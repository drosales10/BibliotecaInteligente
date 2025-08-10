from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    category = Column(String, index=True)
    cover_image_url = Column(String, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Campos para Google Drive (almacenamiento principal)
    drive_file_id = Column(String, nullable=True) # ID del archivo en Google Drive (opcional para libros locales)
    drive_web_link = Column(String, nullable=True) # Link web del archivo en Drive
    drive_letter_folder = Column(String, nullable=True) # Carpeta de letra (A-Z)
    drive_filename = Column(String, nullable=True) # Nombre original del archivo en Drive
    
    # Campo opcional para ruta local temporal (solo durante procesamiento)
    file_path = Column(String, nullable=True) # Ruta temporal local (opcional)
    
    # Campo para indicar si el libro está sincronizado con Google Drive
    synced_to_drive = Column(Boolean, default=False) # Indica si el libro está sincronizado con Drive
    
    # Campos para RAG (Retrieval-Augmented Generation)
    rag_processed = Column(Boolean, default=False) # Indica si el libro ha sido procesado para RAG
    rag_book_id = Column(String, nullable=True) # ID único del libro en el sistema RAG (UUID)
    rag_chunks_count = Column(Integer, nullable=True) # Número de chunks generados para RAG
    rag_processed_date = Column(DateTime(timezone=True), nullable=True) # Fecha de procesamiento RAG