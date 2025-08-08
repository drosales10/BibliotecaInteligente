# Sistema de Modo Oscuro

## Descripción General

Se ha implementado un sistema completo de modo oscuro para la aplicación de Librería Inteligente, que incluye:

- **Toggle automático** con persistencia en localStorage
- **Detección automática** de la preferencia del sistema
- **Transiciones suaves** entre modos
- **Componentes reutilizables** para el toggle
- **Sistema de variables CSS** para consistencia

## Arquitectura del Sistema

### 1. Contexto de Tema (`ThemeContext`)

**Archivo:** `frontend/src/contexts/ThemeContext.js`

El contexto maneja el estado global del tema y proporciona:

- `isDarkMode`: Estado booleano del modo oscuro
- `theme`: String del tema actual ('light' | 'dark')
- `toggleTheme()`: Función para alternar entre modos
- `setTheme(theme)`: Función para establecer un tema específico

**Características:**
- Persistencia automática en localStorage
- Detección de preferencia del sistema
- Manejo de errores robusto
- Aplicación automática de clases CSS

### 2. Componente de Toggle (`DarkModeToggle`)

**Archivo:** `frontend/src/components/DarkModeToggle.js`

Componente reutilizable que proporciona:

- **Iconos animados** (sol y luna)
- **Indicador visual** del estado actual
- **Múltiples tamaños** (small, medium, large)
- **Estados interactivos** (hover, focus, disabled)
- **Accesibilidad completa** (ARIA labels, keyboard navigation)

**Props disponibles:**
- `size`: 'small' | 'medium' | 'large'
- `className`: Clases CSS adicionales
- `disabled`: Estado deshabilitado
- `loading`: Estado de carga

### 3. Sistema de Variables CSS

**Archivo:** `frontend/src/index.css`

El sistema utiliza variables CSS para mantener consistencia:

```css
:root {
  /* Colores principales */
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  
  /* Colores de fondo */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  
  /* Colores de texto */
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  
  /* Colores de borde */
  --border-light: #e2e8f0;
  --border-medium: #cbd5e1;
}

/* Modo oscuro automático */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --border-light: #334155;
    --border-medium: #475569;
  }
}

/* Modo oscuro manual */
.dark-mode :root {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --border-light: #334155;
  --border-medium: #475569;
}
```

## Implementación

### 1. Configuración Inicial

**En `App.js`:**
```javascript
import { ThemeProvider } from './contexts/ThemeContext';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AppModeProvider>
          {/* Resto de la aplicación */}
        </AppModeProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
```

### 2. Uso en Componentes

**En `Header.js`:**
```javascript
import DarkModeToggle from './components/DarkModeToggle';

function Header() {
  return (
    <header className="app-header">
      <div className="header-controls">
        <ModeSelector />
        <DarkModeToggle size="medium" />
        {/* Otros controles */}
      </div>
    </header>
  );
}
```

**Uso del contexto:**
```javascript
import { useTheme } from '../contexts/ThemeContext';

function MiComponente() {
  const { isDarkMode, theme, toggleTheme, setTheme } = useTheme();
  
  return (
    <div>
      <p>Tema actual: {theme}</p>
      <button onClick={toggleTheme}>
        Cambiar a {isDarkMode ? 'claro' : 'oscuro'}
      </button>
    </div>
  );
}
```

## Características del Toggle

### Diseño Visual

- **Forma:** Toggle switch redondeado
- **Iconos:** Sol (modo claro) y luna (modo oscuro)
- **Animaciones:** Transiciones suaves y efectos hover
- **Estados:** Normal, hover, focus, disabled, loading

### Comportamiento

- **Toggle automático:** Alterna entre modos
- **Persistencia:** Guarda preferencia en localStorage
- **Detección automática:** Respeta preferencia del sistema
- **Accesibilidad:** Soporte completo para lectores de pantalla

### Responsive Design

- **Móvil:** Tamaños adaptados para pantallas pequeñas
- **Tablet:** Optimización para pantallas medianas
- **Desktop:** Tamaños completos con efectos mejorados

## Estilos y Animaciones

### Transiciones

```css
.dark-mode-toggle {
  transition: all var(--transition-normal);
}

.dark-mode-toggle:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

### Animaciones de Iconos

```css
.dark-mode-toggle__icon--sun {
  opacity: 1;
  transform: scale(1) rotate(0deg);
}

.dark-mode-toggle:has(.dark-mode-toggle__indicator[data-active="true"]) .dark-mode-toggle__icon--sun {
  opacity: 0.3;
  transform: scale(0.8) rotate(-90deg);
}
```

### Indicador de Estado

```css
.dark-mode-toggle__indicator {
  position: absolute;
  transition: all var(--transition-normal);
}

.dark-mode-toggle__indicator[data-active="true"] {
  left: calc(50% + 0.125rem);
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
}
```

## Integración con Componentes Existentes

### Componentes Actualizados

1. **Header:** Incluye el toggle del modo oscuro
2. **App.css:** Utiliza variables CSS para temas
3. **Index.css:** Sistema global de variables
4. **Todos los componentes:** Compatibles con modo oscuro

### Compatibilidad

- **Vue 2 → Vue 3:** No aplicable (es React)
- **Componentes existentes:** Compatibles automáticamente
- **Nuevos componentes:** Utilizan el sistema de variables

## Uso Avanzado

### Personalización del Toggle

```javascript
// Tamaños disponibles
<DarkModeToggle size="small" />
<DarkModeToggle size="medium" />
<DarkModeToggle size="large" />

// Estados especiales
<DarkModeToggle disabled />
<DarkModeToggle loading />

// Clases personalizadas
<DarkModeToggle className="mi-clase-personalizada" />
```

### Programación del Tema

```javascript
const { setTheme } = useTheme();

// Establecer tema específico
setTheme('dark');
setTheme('light');

// Detectar preferencia del sistema
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
```

### Eventos del Sistema

```javascript
// Escuchar cambios en la preferencia del sistema
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (!localStorage.getItem('theme')) {
    // Solo si no hay tema guardado manualmente
    setTheme(e.matches ? 'dark' : 'light');
  }
});
```

## Testing y Debugging

### Verificación del Estado

```javascript
// Verificar tema actual
console.log('Tema:', theme);
console.log('Modo oscuro:', isDarkMode);

// Verificar localStorage
console.log('Tema guardado:', localStorage.getItem('theme'));

// Verificar clase CSS
console.log('Clase dark-mode:', document.documentElement.classList.contains('dark-mode'));
```

### Componente de Ejemplo

Se incluye `DarkModeExample.js` que demuestra:

- Estado actual del tema
- Controles de toggle
- Información del sistema
- Componentes con tema aplicado
- Funcionalidad de reset

## Beneficios

### Para el Usuario

- **Experiencia personalizada:** Elección del tema preferido
- **Consistencia visual:** Transiciones suaves
- **Accesibilidad:** Soporte para preferencias del sistema
- **Persistencia:** Recordar preferencias entre sesiones

### Para el Desarrollo

- **Mantenibilidad:** Sistema centralizado de temas
- **Escalabilidad:** Fácil agregar nuevos temas
- **Reutilización:** Componentes modulares
- **Consistencia:** Variables CSS unificadas

## Consideraciones Técnicas

### Performance

- **CSS Variables:** Cambios instantáneos sin re-render
- **Transiciones:** Optimizadas con `transform` y `opacity`
- **LocalStorage:** Persistencia eficiente

### Accesibilidad

- **ARIA labels:** Descripción clara del propósito
- **Keyboard navigation:** Soporte completo para teclado
- **Focus management:** Indicadores visuales claros
- **Screen readers:** Compatibilidad total

### Compatibilidad

- **Navegadores modernos:** Soporte completo
- **Fallbacks:** Degradación elegante en navegadores antiguos
- **Mobile:** Optimizado para dispositivos táctiles

## Próximos Pasos

1. **Temas adicionales:** Implementar temas personalizados
2. **Animaciones avanzadas:** Efectos más sofisticados
3. **Configuración:** Panel de preferencias de tema
4. **Analytics:** Seguimiento de preferencias de usuario 