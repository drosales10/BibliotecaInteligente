import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import DriveStatusModal from './components/DriveStatusModal';
import ModeSelector from './components/ModeSelector';
import DarkModeToggle from './components/DarkModeToggle';
import { useAppMode } from './contexts/AppModeContext';
import { useDriveStatus } from './hooks/useDriveStatus';
import './Header.css';

function Header() {
  const { appMode, changeAppMode } = useAppMode();
  const { 
    driveStatus, 
    loading, 
    error, 
    refreshStatus, 
    clearDriveCache, 
    isCacheValid, 
    retryCount 
  } = useDriveStatus();
  
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);

    return () => window.removeEventListener('resize', checkIfMobile);
  }, []);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="app-header">
      <div className="header-logo">
        <h1>📚 Biblioteca Inteligente</h1>
        <div className="header-controls">
          <ModeSelector 
            currentMode={appMode}
            onModeChange={changeAppMode}
          />
          <DarkModeToggle size="medium" />
          {appMode === 'drive' && (
            <DriveStatusModal 
              driveStatus={driveStatus}
              loading={loading}
              error={error}
              refreshStatus={refreshStatus}
              clearDriveCache={clearDriveCache}
              isCacheValid={isCacheValid}
              retryCount={retryCount}
            />
          )}
        </div>
      </div>
      
      {/* Botón hamburguesa para móvil */}
      <button 
        className={`mobile-menu-toggle ${isMobileMenuOpen ? 'active' : ''}`}
        onClick={toggleMobileMenu}
        aria-label="Toggle navigation menu"
        aria-expanded={isMobileMenuOpen}
      >
        <span className="hamburger-line"></span>
        <span className="hamburger-line"></span>
        <span className="hamburger-line"></span>
      </button>

      {/* Navegación principal */}
      <nav className={`header-nav ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        <NavLink 
          to="/" 
          className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          onClick={closeMobileMenu}
        >
          Libros
        </NavLink>
        <NavLink 
          to="/upload" 
          className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          onClick={closeMobileMenu}
        >
          Añadir Libro
        </NavLink>
        <NavLink 
          to="/categories" 
          className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          onClick={closeMobileMenu}
        >
          Etiquetas
        </NavLink>
        <NavLink 
          to="/tools" 
          className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          onClick={closeMobileMenu}
        >
          Herramientas
        </NavLink>
      </nav>

      {/* Overlay para cerrar menú móvil */}
      {isMobileMenuOpen && (
        <div 
          className="mobile-menu-overlay" 
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}
    </header>
  );
}

export default Header;
