import { useCallback } from 'react';
import { useAppMode } from '../contexts/AppModeContext';

export const useBookService = () => {
  const { appMode, isLocalMode, isDriveMode } = useAppMode();

  const getBooks = useCallback(async () => {
    try {
      if (isLocalMode) {
        const response = await fetch('/api/books');
        if (!response.ok) {
          throw new Error('Error al obtener libros del servidor local');
        }
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch('/api/drive/books');
        if (!response.ok) {
          throw new Error('Error al obtener libros de Google Drive');
        }
        return await response.json();
      }
    } catch (error) {
      console.error('Error en getBooks:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const uploadBook = useCallback(async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      if (isLocalMode) {
        const response = await fetch('/api/books/upload', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          throw new Error('Error al subir libro al servidor local');
        }
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch('/api/drive/books/upload', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          throw new Error('Error al subir libro a Google Drive');
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
        const response = await fetch(`/api/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro del servidor local');
        }
        return await response.json();
      } else if (isDriveMode) {
        const response = await fetch(`/api/drive/books/${bookId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error('Error al eliminar libro de Google Drive');
        }
        return await response.json();
      }
    } catch (error) {
      console.error('Error en deleteBook:', error);
      throw error;
    }
  }, [isLocalMode, isDriveMode]);

  const getBookContent = useCallback(async (bookId) => {
    try {
      if (isLocalMode) {
        const response = await fetch(`/api/books/${bookId}/content`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro local');
        }
        return await response.text();
      } else if (isDriveMode) {
        const response = await fetch(`/api/drive/books/${bookId}/content`);
        if (!response.ok) {
          throw new Error('Error al obtener contenido del libro de Drive');
        }
        return await response.text();
      }
    } catch (error) {
      console.error('Error en getBookContent:', error);
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
  };
}; 