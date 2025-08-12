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
      console.log('🔄 Cambiando modo de aplicación:', { from: appMode, to: newMode });
      console.log('🔍 Valores que se establecerán:', {
        newMode,
        isLocalMode: newMode === 'local',
        isDriveMode: newMode === 'drive'
      });
      setAppMode(newMode);
      localStorage.setItem('appMode', newMode);
      console.log('✅ Modo de aplicación cambiado exitosamente a:', newMode);
    } catch (error) {
      console.error('Error al cambiar modo de aplicación:', error);
    }
  };

  const value = {
    appMode,
    changeAppMode,
    isLocalMode: appMode === 'local',
    isDriveMode: appMode === 'drive'
  };

  // Log del valor del contexto
  console.log('🔍 AppModeContext value:', value);

  return (
    <AppModeContext.Provider value={value}>
      {children}
    </AppModeContext.Provider>
  );
}; 