import { useCallback } from 'react';
import { useAppMode } from '../contexts/AppModeContext';

// URL base del backend
const BACKEND_URL = 'http://localhost:8001';

export const useBookService = () => {
  const { appMode, isLocalMode, isDriveMode } = useAppMode();

  const getBooks = useCallback(async (category = null, search = null, page = 1, perPage = 20) => {
    try {
      if (isLocalMode) {
        let url = `${BACKEND_URL}/api/books/`;
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (search) params.append('search', search);
        params.append('page', page.toString());
        params.append('per_page', perPage.toString());
        
        const response = await fetch(`${url}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error('Error al obtener libros del servidor local');
        }
        const data = await response.json();
        return data;
      } else if (isDriveMode) {
        let url = `${BACKEND_URL}/api/drive/books/`;
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (search) params.append('search', search);
        params.append('page', page.toString());
        params.append('per_page', perPage.toString());
        
        const response = await fetch(`${url}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error('Error al obtener libros de Google Drive');
        }
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error('❌ Error en getBooks:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const uploadBook = useCallback(async (file) => {
    try {
      const formData = new FormData();
      formData.append('book_file', file);

      if (isLocalMode) {
        const response = await fetch(`${BACKEND_URL}/api/upload-book-local/`, {
          method: 'POST',
          body: formData,
        });
        
        if (response.status === 409) {
          // Libro duplicado
          const errorData = await response.json();
          return {
            success: false,
            isDuplicate: true,
            detail: errorData.detail || 'Libro duplicado',
            title: errorData.title,
            author: errorData.author
          };
        }
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch(`${BACKEND_URL}/api/drive/books/upload`, {
          method: 'POST',
          body: formData,
        });
        
        if (response.status === 409) {
          // Libro duplicado
          const errorData = await response.json();
          return {
            success: false,
            isDuplicate: true,
            detail: errorData.detail || 'Libro duplicado',
            title: errorData.title,
            author: errorData.author
          };
        }
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      }
    } catch (error) {
      console.error('Error en uploadBook:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const deleteBook = useCallback(async (bookId) => {
    try {
      if (isLocalMode) {
        const response = await fetch(`${BACKEND_URL}/api/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro del servidor local');
        }
        return response;
      } else if (isDriveMode) {
        const response = await fetch(`${BACKEND_URL}/api/drive/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro de Google Drive');
        }
        return response;
      }
    } catch (error) {
      console.error('Error en deleteBook:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const getBookContent = useCallback(async (bookId) => {
    try {
      if (isLocalMode) {
        const response = await fetch(`${BACKEND_URL}/api/books/download/${bookId}`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro local');
        }
        return await response.blob(); // Cambiar de text() a blob() para archivos binarios
      } else if (isDriveMode) {
        const response = await fetch(`${BACKEND_URL}/api/drive/books/${bookId}/content`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro de Drive');
        }
        return await response.blob(); // Cambiar de json() a blob() para archivos binarios
      }
    } catch (error) {
      console.error('Error en getBookContent:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const getCategories = useCallback(async () => {
    try {
      if (isLocalMode) {
        const response = await fetch(`${BACKEND_URL}/api/categories/`);
        if (!response.ok) {
          throw new Error('Error al obtener categorías del servidor local');
        }
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch(`${BACKEND_URL}/api/drive/categories/`);
        if (!response.ok) {
          throw new Error('Error al obtener categorías de Google Drive');
        }
        return await response.json();
      }
    } catch (error) {
      console.error('Error en getCategories:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const updateBook = useCallback(async (bookId, bookData) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookData)
      });

      if (!response.ok) {
        throw new Error('Error al actualizar el libro');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en updateBook:', error);
      throw error;
    }
  }, []);

  const updateBookCover = useCallback(async (bookId, coverFile) => {
    try {
      const formData = new FormData();
      formData.append('cover_file', coverFile);

      const response = await fetch(`${BACKEND_URL}/api/books/${bookId}/update-cover`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Error al actualizar la portada');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en updateBookCover:', error);
      throw error;
    }
  }, []);

  const createCategory = useCallback(async (categoryName) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/categories/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: categoryName })
      });

      if (!response.ok) {
        throw new Error('Error al crear la categoría');
      }

      return await response.json();
    } catch (error) {
      console.error('Error en createCategory:', error);
      throw error;
    }
  }, []);

  const openLocalBook = useCallback(async (bookId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/books/${bookId}/open`);
      
      if (!response.ok) {
        throw new Error('Error al abrir el libro');
      }

      return await response.blob();
    } catch (error) {
      console.error('Error en openLocalBook:', error);
      throw error;
    }
  }, []);

  const cleanupTempFiles = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleanup-temp-files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al limpiar archivos temporales');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error limpiando archivos temporales:', error);
      throw error;
    }
  }, []);

  return {
    appMode,
    isLocalMode,
    isDriveMode,
    getBooks,
    uploadBook,
    deleteBook,
    getBookContent,
    getCategories,
    updateBook,
    updateBookCover,
    createCategory,
    openLocalBook,
    cleanupTempFiles,
  };
}; 