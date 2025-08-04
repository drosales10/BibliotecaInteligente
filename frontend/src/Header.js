import React from 'react';
import { NavLink } from 'react-router-dom';
import DriveStatusIndicator from './components/DriveStatusIndicator';
import ModeSelector from './components/ModeSelector';
import { useAppMode } from './contexts/AppModeContext';
import './Header.css';

function Header() {
  const { appMode, changeAppMode } = useAppMode();

  return (
    <header className="app-header">
      <div className="header-logo">
        <h1>📚 Librería Inteligente</h1>
        <div className="header-controls">
          <ModeSelector 
            currentMode={appMode}
            onModeChange={changeAppMode}
          />
          {appMode === 'drive' && <DriveStatusIndicator />}
        </div>
      </div>
      <nav className="header-nav">
        <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Mi Biblioteca
        </NavLink>
        <NavLink to="/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Añadir Libro
        </NavLink>
        <NavLink to="/etiquetas" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Etiquetas
        </NavLink>
        <NavLink to="/herramientas" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Herramientas
        </NavLink>
      </nav>
    </header>
  );
}

export default Header;
