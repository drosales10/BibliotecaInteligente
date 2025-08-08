import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme debe ser usado dentro de un ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    try {
      // Intentar obtener el tema guardado en localStorage
      const savedTheme = localStorage.getItem('theme');
      
      if (savedTheme) {
        // Si hay un tema guardado, usarlo
        const newDarkMode = savedTheme === 'dark';
        setIsDarkMode(newDarkMode);
        if (newDarkMode) {
          document.documentElement.classList.add('dark-mode');
        } else {
          document.documentElement.classList.remove('dark-mode');
        }
      } else {
        // Si no hay tema guardado, usar la preferencia del sistema
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setIsDarkMode(prefersDark);
        if (prefersDark) {
          document.documentElement.classList.add('dark-mode');
        }
      }
    } catch (error) {
      console.error('Error al cargar tema:', error);
      setIsDarkMode(false);
    }
  }, []);

  const toggleTheme = () => {
    try {
      const newDarkMode = !isDarkMode;
      setIsDarkMode(newDarkMode);
      
      if (newDarkMode) {
        document.documentElement.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
      }
    } catch (error) {
      console.error('Error al cambiar tema:', error);
    }
  };

  const setTheme = (theme) => {
    try {
      const newDarkMode = theme === 'dark';
      setIsDarkMode(newDarkMode);
      
      if (newDarkMode) {
        document.documentElement.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
      }
    } catch (error) {
      console.error('Error al establecer tema:', error);
    }
  };

  const value = {
    isDarkMode,
    toggleTheme,
    setTheme,
    theme: isDarkMode ? 'dark' : 'light'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}; 