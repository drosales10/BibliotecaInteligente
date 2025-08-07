import React from 'react';
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

  return (
    <header className="app-header">
      <div className="header-logo">
        <h1>📚 Librería Inteligente</h1>
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
      <nav className="header-nav">
        <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Mi Biblioteca
        </NavLink>
        <NavLink to="/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Añadir Libro
        </NavLink>
        <NavLink to="/categories" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Etiquetas
        </NavLink>
        <NavLink to="/tools" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          Herramientas
        </NavLink>
      </nav>
    </header>
  );
}

export default Header;
