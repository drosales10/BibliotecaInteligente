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
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedMode = localStorage.getItem('appMode') || 'local';
    setAppMode(savedMode);
    setIsLoading(false);
  }, []);

  const changeAppMode = (newMode) => {
    setAppMode(newMode);
    localStorage.setItem('appMode', newMode);
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