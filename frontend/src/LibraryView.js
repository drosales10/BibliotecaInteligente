import React, { useState, useEffect, useCallback } from 'react';
import './LibraryView.css';

// Hook personalizado para debounce
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  return debouncedValue;
};


// Componente para la portada (con fallback a genérica)
const BookCover = ({ src, alt, title }) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false); // Resetear el error cuando la imagen cambia
  }, [src]);

  const handleError = () => {
    setHasError(true);
  };

  if (hasError || !src) {
    const initial = title ? title[0].toUpperCase() : '?';
    return (
      <div className="generic-cover">
        <span className="generic-cover-initial">{initial}</span>
      </div>
    );
  }

  return <img src={src} alt={alt} className="book-cover" onError={handleError} />;
};


function LibraryView() {
  const [books, setBooks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/categories/');
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (err) {
      console.error('No se pudieron cargar las categorías.');
    }
  }, []);

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError('');
    
    const params = new URLSearchParams();
    if (activeCategory) {
      params.append('category', activeCategory);
    }
    if (debouncedSearchTerm) {
      params.append('search', debouncedSearchTerm);
    }

    const url = `http://localhost:8001/books/?${params.toString()}`;
    
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setBooks(data);
      } else {
        setError('No se pudieron cargar los libros.');
      }
    } catch (err) {
      setError('Error de conexión al cargar la biblioteca.');
    } finally {
      setLoading(false);
    }
  }, [activeCategory, debouncedSearchTerm]);

  // Efecto combinado para cargar datos
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  const handleCategoryClick = (category) => {
    setActiveCategory(category);
    setSearchTerm(''); // Limpiar búsqueda al cambiar de categoría
  };

  const handleDeleteBook = async (bookId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este libro?')) {
      try {
        const response = await fetch(`http://localhost:8001/books/${bookId}`, { method: 'DELETE' });
        if (response.ok) {
          setBooks(prevBooks => prevBooks.filter(b => b.id !== bookId));
          fetchCategories();
        } else {
          alert('No se pudo eliminar el libro.');
        }
      } catch (err) {
        alert('Error de conexión al intentar eliminar el libro.');
      }
    }
  };

  const handleDeleteCategory = async (categoryName) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar la categoría "${categoryName}" y TODOS sus libros? Esta acción no se puede deshacer.`)) {
      try {
        const response = await fetch(`http://localhost:8001/categories/${encodeURIComponent(categoryName)}`, { method: 'DELETE' });
        if (response.ok) {
          setActiveCategory(null);
          fetchCategories();
          fetchBooks();
        } else {
          alert('No se pudo eliminar la categoría.');
        }
      } catch (err) {
        alert('Error de conexión al intentar eliminar la categoría.');
      }
    }
  };

  return (
    <div className="library-container">
      <h2>Mi Biblioteca</h2>
      
      <div className="controls-container">
        <input
          type="text"
          placeholder="Buscar por título, autor o categoría..."
          className="search-bar"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="category-filters">
        <button onClick={() => handleCategoryClick(null)} className={!activeCategory ? 'active' : ''}>Todas</button>
        {categories.map((category) => (
          <div key={category} className="category-chip">
            <button onClick={() => handleCategoryClick(category)} className={activeCategory === category ? 'active' : ''}>
              {category}
            </button>
            <button onClick={() => handleDeleteCategory(category)} className="delete-chip-btn" title={`Eliminar categoría '${category}'`}>×</button>
          </div>
        ))}
      </div>

      {error && <p className="error-message">{error}</p>}
      {loading && <p>Cargando libros...</p>}
      {!loading && books.length === 0 && !error && <p>No se encontraron libros que coincidan con tu búsqueda.</p>}

      <div className="book-grid">
        {books.map((book) => (
          <div key={book.id} className="book-card">
            <button onClick={() => handleDeleteBook(book.id)} className="delete-book-btn" title="Eliminar libro">×</button>
            <BookCover 
              src={book.cover_image_url ? `http://localhost:8001/${book.cover_image_url}` : ''}
              alt={`Portada de ${book.title}`}
              title={book.title}
            />
            <div className="book-card-info">
              <h3>{book.title}</h3>
              <p>{book.author}</p>
              <span>{book.category}</span>
            </div>
            <a href={`http://localhost:8001/books/download/${book.id}`} className="download-button" target="_blank" rel="noopener noreferrer">Abrir/Descargar</a>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LibraryView;
