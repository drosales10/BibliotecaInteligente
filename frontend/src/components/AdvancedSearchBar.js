import React, { useState, useRef, useEffect } from 'react';
import './AdvancedSearchBar.css';

const AdvancedSearchBar = ({ 
  searchTerm, 
  onSearchChange, 
  onClear, 
  onToggleAdvanced, 
  isAdvancedMode, 
  suggestions, 
  searchHistory, 
  isLoading,
  placeholder = "Buscar libros...", 
  className = "" 
}) => {

  const [isFocused, setIsFocused] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Función para manejar cambios en el input
  const handleInputChange = (e) => {
    const value = e.target.value;
    onSearchChange(value);
    setSelectedSuggestion(-1);
    
    // Mostrar sugerencias si hay texto
    if (value.trim().length >= 2) {
      setShowSuggestions(true);
      setShowHistory(false);
    } else {
      setShowSuggestions(false);
      setShowHistory(false);
    }
  };

  // Función para manejar el foco
  const handleFocus = () => {
    setIsFocused(true);
    if (searchTerm.trim().length >= 2) {
      setShowSuggestions(true);
    } else if (searchHistory && searchHistory.length > 0) {
      setShowHistory(true);
    }
  };

  // Función para manejar la pérdida de foco
  const handleBlur = () => {
    setIsFocused(false);
    // Delay para permitir clicks en sugerencias
    setTimeout(() => {
      setShowSuggestions(false);
      setShowHistory(false);
      setSelectedSuggestion(-1);
    }, 200);
  };

  // Función para manejar la búsqueda
  const handleSearch = (term = searchTerm) => {
    if (term.trim()) {
      onSearchChange(term);
      setShowHistory(false);
      setSelectedSuggestion(-1);
      inputRef.current?.blur();
    }
  };

  // Función para manejar la tecla Enter
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedSuggestion >= 0 && suggestions && suggestions[selectedSuggestion]) {
        const selectedTerm = suggestions[selectedSuggestion];
        onSearchChange(selectedTerm);
        handleSearch(selectedTerm);
      } else {
        handleSearch();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (suggestions) {
        setSelectedSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedSuggestion(prev => prev > 0 ? prev - 1 : -1);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setShowHistory(false);
      setSelectedSuggestion(-1);
      inputRef.current?.blur();
    }
  };

  // Función para seleccionar sugerencia
  const handleSuggestionClick = (suggestion) => {
    onSearchChange(suggestion);
    handleSearch(suggestion);
  };

  // Función para seleccionar del historial
  const handleHistoryClick = (historyItem) => {
    onSearchChange(historyItem.term);
    handleSearch(historyItem.term);
  };

  // Función para limpiar búsqueda
  const handleClear = () => {
    onClear();
    setShowSuggestions(false);
    setShowHistory(false);
    setSelectedSuggestion(-1);
    inputRef.current?.focus();
  };

  // Función para activar modo avanzado
  const toggleAdvancedMode = () => {
    onToggleAdvanced();
  };

  // Efecto para manejar clicks fuera del componente
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
        setShowHistory(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Efecto para scroll a sugerencia seleccionada
  useEffect(() => {
    if (selectedSuggestion >= 0 && suggestionsRef.current) {
      const selectedElement = suggestionsRef.current.querySelector('.suggestion-item.selected');
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedSuggestion]);

  return (
    <div className={`advanced-search-bar ${className}`}>
      <div className="search-input-container">
        {/* Icono de búsqueda */}
        <div className="search-icon">
          {isLoading ? (
            <div className="search-spinner">
              <div className="spinner"></div>
            </div>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          )}
        </div>

        {/* Input de búsqueda */}
        <input
          ref={inputRef}
          type="text"
          value={searchTerm || ''}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="search-input"
          aria-label="Buscar libros"
        />

        {/* Botón de limpiar */}
        {searchTerm && (
          <button
            type="button"
            onClick={handleClear}
            className="clear-button"
            aria-label="Limpiar búsqueda"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {/* Botón de búsqueda */}
        <button
          type="button"
          onClick={() => handleSearch()}
          className="search-button"
          disabled={!searchTerm || !searchTerm.trim() || isLoading}
          aria-label="Buscar"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m9 18 6-6-6-6" />
          </svg>
        </button>

        {/* Botón de modo avanzado */}
        <button
          type="button"
          onClick={toggleAdvancedMode}
          className={`advanced-mode-button ${isAdvancedMode ? 'active' : ''}`}
          aria-label="Modo de búsqueda avanzada"
          title="Búsqueda avanzada"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
            <path d="M8 11h6" />
            <path d="M8 7h10" />
            <path d="M8 15h4" />
          </svg>
        </button>
      </div>

      {/* Panel de sugerencias e historial */}
      {(showSuggestions || showHistory) && (
        <div ref={suggestionsRef} className="suggestions-panel">
          {showSuggestions && suggestions && suggestions.length > 0 && (
            <div className="suggestions-section">
              <div className="section-header">
                <span>Sugerencias</span>
              </div>
              <div className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className={`suggestion-item ${index === selectedSuggestion ? 'selected' : ''}`}
                    onClick={() => handleSuggestionClick(suggestion)}
                    onMouseEnter={() => setSelectedSuggestion(index)}
                  >
                    <div className="suggestion-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="m21 21-4.35-4.35" />
                      </svg>
                    </div>
                    <span className="suggestion-text">{suggestion}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {showHistory && searchHistory && searchHistory.length > 0 && (
            <div className="history-section">
              <div className="section-header">
                <span>Búsquedas recientes</span>
                <button
                  type="button"
                  className="clear-history-button"
                  onClick={() => setShowHistory(false)}
                  aria-label="Cerrar historial"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
              <div className="history-list">
                {searchHistory.slice(0, 5).map((historyItem, index) => (
                  <div
                    key={index}
                    className="history-item"
                    onClick={() => handleHistoryClick(historyItem)}
                  >
                    <div className="history-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
                      </svg>
                    </div>
                    <div className="history-content">
                      <span className="history-term">{historyItem.term}</span>
                      <span className="history-meta">
                        {historyItem.resultCount} resultados • {new Date(historyItem.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {showSuggestions && (!suggestions || suggestions.length === 0) && searchTerm && searchTerm.trim().length >= 2 && (
            <div className="no-suggestions">
              <span>No se encontraron sugerencias para "{searchTerm}"</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvancedSearchBar; 