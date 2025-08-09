import React, { useState, useEffect } from 'react';
import './SearchFilters.css';

const SearchFilters = ({ 
  filters, 
  onFiltersChange, 
  onClearFilters, 
  className = "" 
}) => {

  const [filterMetadata, setFilterMetadata] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    basic: true,
    advanced: false,
    dates: false
  });

  // Cargar metadatos de filtros
  useEffect(() => {
    const loadFilterMetadata = async () => {
      try {
        // Metadatos básicos por ahora
        const metadata = {
          categories: ['Ficción', 'No Ficción', 'Ciencia', 'Historia', 'Tecnología'],
          authors: [],
          fileTypes: ['pdf', 'epub', 'txt'],
          sources: ['local', 'drive']
        };
        setFilterMetadata(metadata);
      } catch (error) {
        console.error('Error loading filter metadata:', error);
      }
    };

    loadFilterMetadata();
  }, []);

  // Función para alternar sección expandida
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Función para manejar cambios en filtros
  const handleFilterChange = (filterName, value) => {
    onFiltersChange(filterName, value);
  };

  // Función para limpiar todos los filtros
  const handleClearAll = () => {
    onClearFilters();
  };

  // Función para limpiar filtro específico
  const handleClearFilter = (filterName) => {
    onFiltersChange(filterName, '');
  };

  return (
    <div className={`search-filters ${className}`}>
      <div className="filters-header">
        <h3>Filtros de Búsqueda</h3>
        <div className="filters-actions">
          {Object.values(filters).some(value => value && value !== '') && (
            <button
              type="button"
              onClick={handleClearAll}
              className="clear-all-button"
              title="Limpiar todos los filtros"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
              Limpiar Todo
            </button>
          )}
        </div>
      </div>

      <div className="filters-content">
        {/* Filtros básicos */}
        <div className="filter-section">
          <div 
            className="section-header"
            onClick={() => toggleSection('basic')}
          >
            <h4>Filtros Básicos</h4>
            <svg 
              className={`expand-icon ${expandedSections.basic ? 'expanded' : ''}`}
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </div>
          
          {expandedSections.basic && (
            <div className="section-content">
              {/* Categoría */}
              <div className="filter-group">
                <label htmlFor="category-filter">Categoría</label>
                <select
                  id="category-filter"
                  value={filters.category || ''}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  className="filter-select"
                >
                  <option value="">Todas las categorías</option>
                  {filterMetadata?.categories?.map(category => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
                {filters.category && (
                  <button
                    type="button"
                    onClick={() => handleClearFilter('category')}
                    className="clear-filter-button"
                    title="Limpiar categoría"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Autor */}
              <div className="filter-group">
                <label htmlFor="author-filter">Autor</label>
                <input
                  id="author-filter"
                  type="text"
                  value={filters.author || ''}
                  onChange={(e) => handleFilterChange('author', e.target.value)}
                  placeholder="Buscar por autor..."
                  className="filter-input"
                />
                {filters.author && (
                  <button
                    type="button"
                    onClick={() => handleClearFilter('author')}
                    className="clear-filter-button"
                    title="Limpiar autor"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Filtros avanzados */}
        <div className="filter-section">
          <div 
            className="section-header"
            onClick={() => toggleSection('advanced')}
          >
            <h4>Filtros Avanzados</h4>
            <svg 
              className={`expand-icon ${expandedSections.advanced ? 'expanded' : ''}`}
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </div>
          
          {expandedSections.advanced && (
            <div className="section-content">
              {/* Tipo de archivo */}
              <div className="filter-group">
                <label htmlFor="fileType-filter">Tipo de archivo</label>
                <select
                  id="fileType-filter"
                  value={filters.fileType || ''}
                  onChange={(e) => handleFilterChange('fileType', e.target.value)}
                  className="filter-select"
                >
                  <option value="">Todos los tipos</option>
                  {filterMetadata?.fileTypes?.map(fileType => (
                    <option key={fileType} value={fileType}>
                      {fileType.toUpperCase()}
                    </option>
                  ))}
                </select>
                {filters.fileType && (
                  <button
                    type="button"
                    onClick={() => handleClearFilter('fileType')}
                    className="clear-filter-button"
                    title="Limpiar tipo de archivo"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Fuente */}
              <div className="filter-group">
                <label htmlFor="source-filter">Fuente</label>
                <select
                  id="source-filter"
                  value={filters.source || ''}
                  onChange={(e) => handleFilterChange('source', e.target.value)}
                  className="filter-select"
                >
                  <option value="">Todas las fuentes</option>
                  {filterMetadata?.sources?.map(source => (
                    <option key={source} value={source}>
                      {source === 'local' ? 'Local' : 'Google Drive'}
                    </option>
                  ))}
                </select>
                {filters.source && (
                  <button
                    type="button"
                    onClick={() => handleClearFilter('source')}
                    className="clear-filter-button"
                    title="Limpiar fuente"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Checkboxes */}
              <div className="filter-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.hasCover || false}
                    onChange={(e) => handleFilterChange('hasCover', e.target.checked)}
                    className="filter-checkbox"
                  />
                  <span className="checkbox-text">Con portada</span>
                </label>
                
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={filters.hasFile || false}
                    onChange={(e) => handleFilterChange('hasFile', e.target.checked)}
                    className="filter-checkbox"
                  />
                  <span className="checkbox-text">Con archivo</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Filtros de fecha */}
        <div className="filter-section">
          <div 
            className="section-header"
            onClick={() => toggleSection('dates')}
          >
            <h4>Rango de Fechas</h4>
            <svg 
              className={`expand-icon ${expandedSections.dates ? 'expanded' : ''}`}
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </div>
          
          {expandedSections.dates && (
            <div className="section-content">
              <div className="date-range-group">
                <div className="filter-group">
                  <label htmlFor="dateFrom-filter">Desde</label>
                  <input
                    id="dateFrom-filter"
                    type="date"
                    value={filters.dateFrom || ''}
                    onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                    className="filter-input"
                  />
                  {filters.dateFrom && (
                    <button
                      type="button"
                      onClick={() => handleClearFilter('dateFrom')}
                      className="clear-filter-button"
                      title="Limpiar fecha desde"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="filter-group">
                  <label htmlFor="dateTo-filter">Hasta</label>
                  <input
                    id="dateTo-filter"
                    type="date"
                    value={filters.dateTo || ''}
                    onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                    className="filter-input"
                  />
                  {filters.dateTo && (
                    <button
                      type="button"
                      onClick={() => handleClearFilter('dateTo')}
                      className="clear-filter-button"
                      title="Limpiar fecha hasta"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchFilters; 