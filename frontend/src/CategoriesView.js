import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './CategoriesView.css';
import { getBackendUrl } from './config/api';

function CategoriesView() {
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${getBackendUrl()}/api/categories/`);
        if (response.ok) {
          const data = await response.json();
          setCategories(data);
        } else {
          setError('No se pudieron cargar las categorías.');
        }
      } catch (err) {
        setError('Error de conexión al cargar las categorías.');
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
  }, []);

  return (
    <div className="categories-container">
      <h2>Todas las Etiquetas</h2>
      {loading && <p>Cargando etiquetas...</p>}
      {error && <p className="error-message">{error}</p>}
      {!loading && (
        <div className="categories-grid">
          {categories.map((category) => (
            <Link to={`/?category=${encodeURIComponent(category)}`} key={category} className="category-card">
              {category}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default CategoriesView;
