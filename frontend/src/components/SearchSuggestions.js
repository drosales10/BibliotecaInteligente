import React from 'react';
import './SearchSuggestions.css';

const SearchSuggestions = ({ suggestions = [], onSelect, className = "" }) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const handleSuggestionClick = (suggestion) => {
    if (onSelect) {
      onSelect(suggestion);
    }
  };

  const handleKeyDown = (e, suggestion) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSuggestionClick(suggestion);
    }
  };

  return (
    <div className={`search-suggestions ${className}`}>
      <div className="suggestions-header">
        <span>Sugerencias de búsqueda</span>
      </div>
      
      <div className="suggestions-list">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="suggestion-item"
            onClick={() => handleSuggestionClick(suggestion)}
            onKeyDown={(e) => handleKeyDown(e, suggestion)}
            tabIndex={0}
            role="button"
            aria-label={`Seleccionar sugerencia: ${suggestion}`}
          >
            <div className="suggestion-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </div>
            
            <span className="suggestion-text">{suggestion}</span>
            
            <div className="suggestion-actions">
              <button
                type="button"
                className="suggestion-action-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleSuggestionClick(suggestion);
                }}
                title="Seleccionar sugerencia"
                aria-label={`Seleccionar: ${suggestion}`}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="m9 18 6-6-6-6" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <div className="suggestions-footer">
        <span className="footer-text">
          Usa las flechas ↑↓ para navegar, Enter para seleccionar
        </span>
      </div>
    </div>
  );
};

export default SearchSuggestions; 