import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import DarkModeToggle from './DarkModeToggle';
import Card from './Card';
import Button from './Button';
import Input from './Input';
import './DarkModeExample.css';

const DarkModeExample = () => {
  const { isDarkMode, theme, toggleTheme, setTheme } = useTheme();

  return (
    <div className="dark-mode-example">
      <Card variant="elevated" className="dark-mode-example__card">
        <Card.Header>
          <Card.Title>Ejemplo de Modo Oscuro</Card.Title>
          <Card.Subtitle>
            Demostración del sistema de temas con toggle automático
          </Card.Subtitle>
        </Card.Header>
        
        <Card.Body>
          <div className="dark-mode-example__content">
            <div className="dark-mode-example__section">
              <h3>Estado Actual</h3>
              <p>
                <strong>Tema actual:</strong> {theme === 'dark' ? 'Oscuro' : 'Claro'}
              </p>
              <p>
                <strong>Modo oscuro activo:</strong> {isDarkMode ? 'Sí' : 'No'}
              </p>
            </div>

            <div className="dark-mode-example__section">
              <h3>Controles de Tema</h3>
              <div className="dark-mode-example__controls">
                <div className="dark-mode-example__toggle-group">
                  <label>Toggle automático:</label>
                  <DarkModeToggle size="medium" />
                </div>
                
                <div className="dark-mode-example__button-group">
                  <Button
                    variant="primary"
                    size="small"
                    onClick={() => setTheme('light')}
                    disabled={!isDarkMode}
                  >
                    Modo Claro
                  </Button>
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => setTheme('dark')}
                    disabled={isDarkMode}
                  >
                    Modo Oscuro
                  </Button>
                </div>
              </div>
            </div>

            <div className="dark-mode-example__section">
              <h3>Componentes con Tema</h3>
              <div className="dark-mode-example__components">
                <Input
                  label="Campo de texto"
                  placeholder="Escribe algo aquí..."
                  fullWidth
                />
                
                <div className="dark-mode-example__buttons">
                  <Button variant="primary">Botón Primario</Button>
                  <Button variant="secondary">Botón Secundario</Button>
                  <Button variant="outline">Botón Outline</Button>
                </div>
              </div>
            </div>

            <div className="dark-mode-example__section">
              <h3>Información del Sistema</h3>
              <div className="dark-mode-example__info">
                <p>
                  <strong>Preferencia del sistema:</strong> {
                    window.matchMedia('(prefers-color-scheme: dark)').matches 
                      ? 'Oscuro' 
                      : 'Claro'
                  }
                </p>
                <p>
                  <strong>Tema guardado:</strong> {
                    localStorage.getItem('theme') || 'No guardado (usa preferencia del sistema)'
                  }
                </p>
                <p>
                  <strong>Clase CSS aplicada:</strong> {
                    document.documentElement.classList.contains('dark-mode') 
                      ? 'dark-mode' 
                      : 'ninguna'
                  }
                </p>
              </div>
            </div>
          </div>
        </Card.Body>
        
        <Card.Footer>
          <div className="dark-mode-example__footer">
            <p>
              El tema se guarda automáticamente en localStorage y se restaura al recargar la página.
            </p>
            <Button
              variant="ghost"
              size="small"
              onClick={() => {
                localStorage.removeItem('theme');
                window.location.reload();
              }}
            >
              Resetear Tema
            </Button>
          </div>
        </Card.Footer>
      </Card>
    </div>
  );
};

export default DarkModeExample; 