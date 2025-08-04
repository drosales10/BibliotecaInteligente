import React, { createContext, useContext, useState, useEffect } from 'react';

const AppModeContext = createContext();

export const useAppMode = () => {
  const context = useContext(AppModeContext);
  if (!context) {
    throw new Error('useAppMode debe ser usado dentro de un AppModeProvider');
  }
  return context;
};

export const AppModeProvider = ({ children }) => {
  const [appMode, setAppMode] = useState('local');
  const [isLoading, setIsLoading] = useState(false); // Cambiar a false por defecto

  useEffect(() => {
    try {
      const savedMode = localStorage.getItem('appMode') || 'local';
      setAppMode(savedMode);
    } catch (error) {
      console.error('Error al cargar modo de aplicación:', error);
      setAppMode('local');
    }
  }, []);

  const changeAppMode = (newMode) => {
    try {
      setAppMode(newMode);
      localStorage.setItem('appMode', newMode);
    } catch (error) {
      console.error('Error al cambiar modo de aplicación:', error);
    }
  };

  const value = {
    appMode,
    changeAppMode,
    isLoading,
    isLocalMode: appMode === 'local',
    isDriveMode: appMode === 'drive'
  };

  return (
    <AppModeContext.Provider value={value}>
      {children}
    </AppModeContext.Provider>
  );
}; 