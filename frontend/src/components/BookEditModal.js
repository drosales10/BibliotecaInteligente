import React, { useState, useRef, useEffect } from 'react';
import './BookEditModal.css';

const BookEditModal = ({ 
  isOpen, 
  onClose, 
  book, 
  onUpdate, 
  categories = [],
  onCategoryCreate 
}) => {
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    category: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [showNewCategoryInput, setShowNewCategoryInput] = useState(false);
  const [localCategories, setLocalCategories] = useState(categories);
  const fileInputRef = useRef(null);

  // Actualizar formulario cuando cambie el libro
  useEffect(() => {
    if (book) {
      setFormData({
        title: book.title || '',
        author: book.author || '',
        category: book.category || ''
      });
      setMessage('');
      setNewCategory('');
      setShowNewCategoryInput(false);
    }
  }, [book]);

  // Sincronizar categorías locales con las props
  useEffect(() => {
    setLocalCategories(categories);
  }, [categories]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch(`http://localhost:8001/api/books/${book.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Error al actualizar el libro');
      }

      const updatedBook = await response.json();
      onUpdate(updatedBook);
      setMessage('✅ Libro actualizado exitosamente');
      
      setTimeout(() => {
        handleClose();
      }, 1500);
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCoverChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setMessage('❌ El archivo debe ser una imagen');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('cover_file', file);

      const response = await fetch(`http://localhost:8001/api/books/${book.id}/update-cover`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Error al actualizar la portada');
      }

      const result = await response.json();
      // Actualizar el libro con la nueva URL de portada
      const updatedBook = { ...book, cover_image_url: result.cover_url };
      onUpdate(updatedBook);
      setMessage('✅ Portada actualizada exitosamente');
      
      // Limpiar el input de archivo
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      setTimeout(() => {
        setMessage('');
      }, 2000);
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.trim()) {
      setMessage('❌ El nombre de la categoría es requerido');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:8001/api/categories/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newCategory.trim() })
      });

      if (!response.ok) {
        throw new Error('Error al crear la categoría');
      }

      const result = await response.json();
      
      // Notificar al componente padre sobre la nueva categoría
      onCategoryCreate(newCategory.trim());
      
      // Actualizar las categorías locales inmediatamente
      setLocalCategories(prev => [...prev, newCategory.trim()]);
      
      // Actualizar el formulario con la nueva categoría
      setFormData(prev => ({ ...prev, category: newCategory.trim() }));
      
      // Limpiar el estado del modal
      setNewCategory('');
      setShowNewCategoryInput(false);
      setMessage('✅ Categoría creada exitosamente');
      
      setTimeout(() => {
        setMessage('');
      }, 2000);
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Función para obtener la URL correcta de la imagen
  const getImageUrl = (imageSrc) => {
    if (!imageSrc) {
      return '';
    }
    
    // Si es una URL completa (Google Drive), usar el endpoint del backend
    if (imageSrc.startsWith('http') && imageSrc.includes('drive.google.com')) {
      // Extraer el file_id de la URL de Google Drive
      if (imageSrc.includes('/file/d/')) {
        const fileId = imageSrc.split('/file/d/')[1].split('/')[0];
        return `http://localhost:8001/api/drive/cover/${fileId}`;
      }
      return imageSrc;
    }
    
    // Si es una ruta local, construir la URL completa
    if (imageSrc.startsWith('/')) {
      return `http://localhost:8001${imageSrc}`;
    }
    
    // Si es solo el nombre del archivo, construir la URL correcta
    return `http://localhost:8001/static/covers/${imageSrc}`;
  };

  const handleOpenBook = async () => {
    try {
      // Verificar si el libro está en modo local o nube
      if (book.source === 'local' || (!book.synced_to_drive && !book.drive_file_id)) {
        // Libro local - abrir en nueva pestaña
        const url = `http://localhost:8001/api/books/download/${book.id}`;
        window.open(url, '_blank');
      } else if (book.source === 'drive' || book.synced_to_drive || book.drive_file_id) {
        // Libro en Google Drive - abrir en nueva pestaña
        const url = `http://localhost:8001/api/drive/books/${book.id}/content`;
        window.open(url, '_blank');
      } else {
        setMessage('❌ No se puede determinar la ubicación del libro');
      }
    } catch (error) {
      setMessage(`❌ Error al abrir el libro: ${error.message}`);
    }
  };

  // Limpiar formulario cuando se cierre el modal
  const handleClose = () => {
    setFormData({
      title: '',
      author: '',
      category: ''
    });
    setMessage('');
    setNewCategory('');
    setShowNewCategoryInput(false);
    setLocalCategories(categories); // Resetear categorías locales
    onClose();
  };

  if (!isOpen || !book) return null;

  return (
    <div className="book-edit-modal-overlay" onClick={handleClose}>
      <div className="book-edit-modal" onClick={(e) => e.stopPropagation()}>
        <div className="book-edit-modal-header">
          <h3>📖 Editar Libro</h3>
          <button 
            className="book-edit-modal-close"
            onClick={handleClose}
            disabled={isLoading}
          >
            ✕
          </button>
        </div>

        <div className="book-edit-modal-body">
          <div className="book-edit-cover-section">
            <div className="book-edit-cover-preview">
              {book.cover_image_url ? (
                <img 
                  src={getImageUrl(book.cover_image_url)} 
                  alt={book.title}
                  className="book-edit-cover-image"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div 
                className="book-edit-cover-placeholder"
                style={{ display: book.cover_image_url ? 'none' : 'flex' }}
              >
                <span>{book.title ? book.title[0].toUpperCase() : '?'}</span>
              </div>
            </div>
            <div className="book-edit-cover-actions">
              <button
                type="button"
                className="book-edit-cover-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                📷 Cambiar Portada
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleCoverChange}
                style={{ display: 'none' }}
              />
            </div>
          </div>

          <form onSubmit={handleSubmit} className="book-edit-form">
            <div className="book-edit-form-group">
              <label htmlFor="title">Título:</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                disabled={isLoading}
              />
            </div>

            <div className="book-edit-form-group">
              <label htmlFor="author">Autor:</label>
              <input
                type="text"
                id="author"
                name="author"
                value={formData.author}
                onChange={handleInputChange}
                required
                disabled={isLoading}
              />
            </div>

            <div className="book-edit-form-group">
              <label htmlFor="category">Categoría:</label>
              <div className="book-edit-category-container">
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  disabled={isLoading || showNewCategoryInput}
                >
                  <option value="">Seleccionar categoría</option>
                  {localCategories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="book-edit-new-category-button"
                  onClick={() => setShowNewCategoryInput(true)}
                  disabled={isLoading}
                >
                  ➕ Nueva
                </button>
              </div>
              
              {showNewCategoryInput && (
                <div className="book-edit-new-category-input">
                  <input
                    type="text"
                    placeholder="Nombre de la nueva categoría"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={handleCreateCategory}
                    disabled={isLoading || !newCategory.trim()}
                  >
                    ✅ Crear
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowNewCategoryInput(false);
                      setNewCategory('');
                    }}
                    disabled={isLoading}
                  >
                    ❌ Cancelar
                  </button>
                </div>
              )}
            </div>

            {book.file_path && (
              <div className="book-edit-actions">
                <button
                  type="button"
                  className="book-edit-open-button"
                  onClick={handleOpenBook}
                  disabled={isLoading}
                >
                  📖 Abrir Libro
                </button>
              </div>
            )}

            {message && (
              <div className={`book-edit-message ${message.includes('✅') ? 'success' : 'error'}`}>
                {message}
              </div>
            )}

            <div className="book-edit-form-actions">
              <button
                type="submit"
                className="book-edit-save-button"
                disabled={isLoading}
              >
                {isLoading ? '💾 Guardando...' : '💾 Guardar Cambios'}
              </button>
              <button
                type="button"
                className="book-edit-cancel-button"
                onClick={handleClose}
                disabled={isLoading}
              >
                ❌ Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default BookEditModal;
