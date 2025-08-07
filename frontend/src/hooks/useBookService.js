import { useCallback } from 'react';
import { useAppMode } from '../contexts/AppModeContext';

// URL base del backend
const BACKEND_URL = 'http://localhost:8001';

export const useBookService = () => {
  const { appMode, isLocalMode, isDriveMode } = useAppMode();

  const getBooks = useCallback(async (category = null, search = null) => {
    try {
      if (isLocalMode) {
        let url = `${BACKEND_URL}/api/books/`;
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (search) params.append('search', search);
        if (params.toString()) url += '?' + params.toString();
        
        const response = await fetch(url);
        
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
        if (params.toString()) url += '?' + params.toString();
        
        const response = await fetch(url);
        
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

  return {
    appMode,
    isLocalMode,
    isDriveMode,
    getBooks,
    uploadBook,
    deleteBook,
    getBookContent,
    getCategories,
  };
}; 