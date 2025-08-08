import React from 'react';
import './FilterChips.css';

const FilterChips = ({ 
  activeFilters, 
  onRemoveFilter, 
  onClearAll, 
  className = "" 
}) => {

  // Función para obtener el icono del filtro
  const getFilterIcon = (filterName) => {
    const icons = {
      category: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3h18v18H3z" />
          <path d="M9 9h6v6H9z" />
        </svg>
      ),
      author: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      ),
      dateFrom: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
      ),
      dateTo: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
      ),
      fileType: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14,2 14,8 20,8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10,9 9,9 8,9" />
        </svg>
      ),
      source: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
        </svg>
      ),
      hasCover: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21,15 16,10 5,21" />
        </svg>
      ),
      hasFile: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14,2 14,8 20,8" />
        </svg>
      )
    };
    
    return icons[filterName] || (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    );
  };

  // Función para obtener el color del filtro
  const getFilterColor = (filterName) => {
    const colors = {
      category: 'var(--primary-color)',
      author: 'var(--success-color)',
      dateFrom: 'var(--warning-color)',
      dateTo: 'var(--warning-color)',
      fileType: 'var(--info-color)',
      source: 'var(--secondary-color)',
      hasCover: 'var(--accent-color)',
      hasFile: 'var(--accent-color)'
    };
    
    return colors[filterName] || 'var(--primary-color)';
  };

  // Función para formatear el valor del filtro
  const formatFilterValue = (filterName, value) => {
    if (filterName === 'hasCover' || filterName === 'hasFile') {
      return value ? 'Sí' : 'No';
    }
    
    if (filterName === 'dateFrom' || filterName === 'dateTo') {
      return new Date(value).toLocaleDateString('es-ES');
    }
    
    if (filterName === 'source') {
      const sourceLabels = {
        local: 'Local',
        drive: 'Google Drive'
      };
      return sourceLabels[value] || value;
    }
    
    if (filterName === 'fileType') {
      return value.toUpperCase();
    }
    
    return value;
  };

  if (!activeFilters || activeFilters.length === 0) {
    return null;
  }

  return (
    <div className={`filter-chips ${className}`}>
      <div className="chips-header">
        <span className="chips-title">Filtros activos ({activeFilters.length})</span>
      </div>
      
      <div className="chips-container">
        {activeFilters.map((filter, index) => (
          <div
            key={`${filter.name}-${index}`}
            className="filter-chip"
            style={{ '--chip-color': getFilterColor(filter.name) }}
          >
            <div className="chip-icon">
              {getFilterIcon(filter.name)}
            </div>
            
            <span className="chip-label">
              {filter.label}
            </span>
            
            <button
              type="button"
              onClick={() => onRemoveFilter(filter.name)}
              className="chip-remove-button"
              title={`Eliminar filtro: ${filter.label}`}
              aria-label={`Eliminar filtro: ${filter.label}`}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      
      {activeFilters.length > 0 && (
        <div className="chips-summary">
          <span className="summary-text">
            Mostrando resultados filtrados
          </span>
        </div>
      )}
    </div>
  );
};

export default FilterChips; 