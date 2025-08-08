from pydantic import BaseModel
from typing import List, Optional, Generic, TypeVar

T = TypeVar('T')

class BookBase(BaseModel):
    title: str
    author: str
    category: str
    cover_image_url: str | None = None
    file_path: Optional[str] = None  # Ahora es opcional

class Book(BookBase):
    id: int
    # Campos para Google Drive (almacenamiento principal)
    drive_file_id: Optional[str] = None  # Opcional para compatibilidad con libros existentes
    drive_web_link: Optional[str] = None
    drive_letter_folder: Optional[str] = None
    drive_filename: Optional[str] = None

    class Config:
        from_attributes = True

class ConversionResponse(BaseModel):
    download_url: str

class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    cover_image_url: Optional[str] = None
    file_path: Optional[str] = None  # Ahora es opcional

class DuplicateInfo(BaseModel):
    is_duplicate: bool
    reason: Optional[str] = None
    existing_book: Optional[dict] = None
    message: str

class BulkUploadResult(BaseModel):
    success: bool
    file: str
    book: Optional[dict] = None
    error: Optional[str] = None
    duplicate_info: Optional[DuplicateInfo] = None

class OptimizationStats(BaseModel):
    total_files: int
    unique_files: int
    duplicate_files: int
    saved_ai_calls: int

class BulkUploadResponse(BaseModel):
    message: str
    total_files: int
    successful: int
    failed: int
    duplicates: int
    successful_books: List[BulkUploadResult]
    failed_files: List[BulkUploadResult]
    duplicate_files: List[BulkUploadResult]
    optimization_stats: OptimizationStats

# Esquemas de paginación
class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationInfo