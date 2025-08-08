import React, { useState } from 'react';
import Button from './Button';
import Card from './Card';
import Input from './Input';

const ExampleUsage = () => {
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState('');

  const handleButtonClick = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    if (e.target.value.length < 3) {
      setInputError('El texto debe tener al menos 3 caracteres');
    } else {
      setInputError('');
    }
  };

  return (
    <div className="example-usage" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--text-primary)' }}>
        Ejemplos de Uso - Componentes Modernos
      </h1>

      {/* Sección de Botones */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Botones</h2>
        
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          <Button variant="primary" icon="📚" onClick={handleButtonClick}>
            Botón Primario
          </Button>
          
          <Button variant="secondary" icon="✅" onClick={handleButtonClick}>
            Botón Secundario
          </Button>
          
          <Button variant="accent" icon="⭐" onClick={handleButtonClick}>
            Botón Acento
          </Button>
          
          <Button variant="outline" icon="📝" onClick={handleButtonClick}>
            Botón Outline
          </Button>
          
          <Button variant="ghost" icon="👁️" onClick={handleButtonClick}>
            Botón Ghost
          </Button>
          
          <Button variant="danger" icon="🗑️" onClick={handleButtonClick}>
            Botón Peligro
          </Button>
          
          <Button variant="primary" loading={loading} onClick={handleButtonClick}>
            {loading ? 'Cargando...' : 'Botón con Loading'}
          </Button>
          
          <Button variant="secondary" disabled onClick={handleButtonClick}>
            Botón Deshabilitado
          </Button>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Tamaños</h3>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <Button variant="primary" size="small">Pequeño</Button>
            <Button variant="primary" size="medium">Mediano</Button>
            <Button variant="primary" size="large">Grande</Button>
          </div>
        </div>
      </section>

      {/* Sección de Tarjetas */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Tarjetas</h2>
        
        <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          {/* Tarjeta Básica */}
          <Card variant="default" hoverable>
            <Card.Body>
              <Card.Title>Tarjeta Básica</Card.Title>
              <Card.Subtitle>Subtítulo de la tarjeta</Card.Subtitle>
              <Card.Content>
                Esta es una tarjeta básica con efecto hover. Contiene información importante
                sobre el contenido que se está mostrando.
              </Card.Content>
            </Card.Body>
          </Card>

          {/* Tarjeta con Header y Footer */}
          <Card variant="elevated" hoverable>
            <Card.Header>Tarjeta con Header</Card.Header>
            <Card.Body>
              <Card.Title>Libro de Ejemplo</Card.Title>
              <Card.Subtitle>Autor del Libro</Card.Subtitle>
              <Card.Content>
                Descripción del libro que se está mostrando en esta tarjeta.
                Puede contener información adicional sobre el contenido.
              </Card.Content>
            </Card.Body>
            <Card.Footer>
              <Card.Actions>
                <Button variant="primary" size="small">Leer</Button>
                <Button variant="outline" size="small">Editar</Button>
              </Card.Actions>
            </Card.Footer>
          </Card>

          {/* Tarjeta con Imagen */}
          <Card variant="outlined" hoverable>
            <Card.Image 
              src="https://via.placeholder.com/300x200/3b82f6/ffffff?text=Imagen+Ejemplo" 
              alt="Imagen de ejemplo"
            />
            <Card.Body>
              <Card.Title>Tarjeta con Imagen</Card.Title>
              <Card.Subtitle>Subtítulo con imagen</Card.Subtitle>
              <Card.Content>
                Esta tarjeta incluye una imagen de ejemplo y muestra cómo se pueden
                combinar diferentes elementos en una sola tarjeta.
              </Card.Content>
            </Card.Body>
          </Card>

          {/* Tarjeta de Estadísticas */}
          <Card variant="stats">
            <Card.Title>1,234</Card.Title>
            <Card.Subtitle>Libros en la Biblioteca</Card.Subtitle>
            <Card.Content>
              Total de libros disponibles en tu biblioteca personal
            </Card.Content>
          </Card>

          {/* Tarjeta de Perfil */}
          <Card variant="profile">
            <Card.Image 
              src="https://via.placeholder.com/120x120/10b981/ffffff?text=👤" 
              alt="Avatar de usuario"
            />
            <Card.Title>Usuario Ejemplo</Card.Title>
            <Card.Subtitle>Lector Avanzado</Card.Subtitle>
            <Card.Content>
              Miembro desde 2023 • 156 libros leídos
            </Card.Content>
          </Card>

          {/* Tarjeta Glass */}
          <Card variant="glass" hoverable>
            <Card.Body>
              <Card.Title>Tarjeta Glass</Card.Title>
              <Card.Subtitle>Efecto de cristal</Card.Subtitle>
              <Card.Content>
                Esta tarjeta utiliza el efecto glass con backdrop blur para crear
                un diseño moderno y elegante.
              </Card.Content>
            </Card.Body>
          </Card>
        </div>
      </section>

      {/* Sección de Inputs */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Campos de Entrada</h2>
        
        <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          <Input
            label="Campo de Texto Básico"
            placeholder="Escribe algo aquí..."
            value={inputValue}
            onChange={handleInputChange}
            error={inputError}
            fullWidth
          />

          <Input
            label="Campo con Icono"
            placeholder="Buscar libros..."
            icon="🔍"
            fullWidth
          />

          <Input
            label="Campo de Búsqueda"
            placeholder="Buscar en la biblioteca..."
            className="modern-input--search"
            fullWidth
          />

          <Input
            label="Campo con Éxito"
            placeholder="Campo válido"
            value="Texto válido"
            success="Campo completado correctamente"
            fullWidth
          />

          <Input
            label="Campo Deshabilitado"
            placeholder="No puedes escribir aquí"
            disabled
            fullWidth
          />

          <Input
            label="Campo Requerido"
            placeholder="Este campo es obligatorio"
            required
            fullWidth
          />
        </div>

        <div style={{ marginTop: '1rem' }}>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Tamaños de Input</h3>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Input
              label="Pequeño"
              placeholder="Input pequeño"
              size="small"
            />
            <Input
              label="Mediano"
              placeholder="Input mediano"
              size="medium"
            />
            <Input
              label="Grande"
              placeholder="Input grande"
              size="large"
            />
          </div>
        </div>
      </section>

      {/* Sección de Combinaciones */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Combinaciones</h2>
        
        <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))' }}>
          {/* Formulario de Ejemplo */}
          <Card variant="elevated">
            <Card.Header>Formulario de Ejemplo</Card.Header>
            <Card.Body>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <Input
                  label="Nombre del Libro"
                  placeholder="Ingresa el título del libro"
                  icon="📖"
                  required
                />
                <Input
                  label="Autor"
                  placeholder="Nombre del autor"
                  icon="✍️"
                  required
                />
                <Input
                  label="Categoría"
                  placeholder="Selecciona una categoría"
                  icon="🏷️"
                />
              </div>
            </Card.Body>
            <Card.Footer>
              <Card.Actions>
                <Button variant="primary" icon="💾">Guardar</Button>
                <Button variant="outline" icon="❌">Cancelar</Button>
              </Card.Actions>
            </Card.Footer>
          </Card>

          {/* Panel de Acciones */}
          <Card variant="outlined">
            <Card.Header>Panel de Acciones</Card.Header>
            <Card.Body>
              <Card.Content>
                Selecciona una acción para continuar con el proceso de gestión de tu biblioteca.
              </Card.Content>
            </Card.Body>
            <Card.Footer>
              <Card.Actions>
                <Button variant="primary" icon="📤">Exportar</Button>
                <Button variant="secondary" icon="📥">Importar</Button>
                <Button variant="accent" icon="🔄">Sincronizar</Button>
                <Button variant="danger" icon="🗑️">Eliminar</Button>
              </Card.Actions>
            </Card.Footer>
          </Card>
        </div>
      </section>

      {/* Sección de Responsive */}
      <section>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Diseño Responsive</h2>
        
        <Card variant="default">
          <Card.Header>Grid Responsive</Card.Header>
          <Card.Body>
            <div style={{ 
              display: 'grid', 
              gap: '1rem', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              marginBottom: '1rem'
            }}>
              <Button variant="primary" size="small">Botón 1</Button>
              <Button variant="secondary" size="small">Botón 2</Button>
              <Button variant="accent" size="small">Botón 3</Button>
              <Button variant="outline" size="small">Botón 4</Button>
            </div>
            
            <Card.Subtitle>Este grid se adapta automáticamente al tamaño de la pantalla</Card.Subtitle>
          </Card.Body>
        </Card>
      </section>
    </div>
  );
};

export default ExampleUsage; 