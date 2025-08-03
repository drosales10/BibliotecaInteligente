from pydantic import BaseModel
from typing import List, Optional

class BookBase(BaseModel):
    title: str
    author: str
    category: str
    cover_image_url: str | None = None
    file_path: str

class Book(BookBase):
    id: int

    class Config:
        from_attributes = True

class ConversionResponse(BaseModel):
    download_url: str

class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    cover_image_url: Optional[str] = None
    file_path: str

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