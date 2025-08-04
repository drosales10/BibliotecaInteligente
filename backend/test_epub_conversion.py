#!/usr/bin/env python3
"""
Script de prueba para crear un EPUB simple y probar la conversión a PDF
"""

import os
import tempfile
from ebooklib import epub

def create_test_epub():
    """Crea un EPUB de prueba simple"""
    
    # Crear un libro EPUB
    book = epub.EpubBook()
    
    # Metadatos
    book.set_identifier('id123456')
    book.set_title('Libro de Prueba')
    book.set_language('es')
    book.add_author('Autor de Prueba')
    
    # Crear contenido
    c1 = epub.EpubHtml(title='Introducción', file_name='intro.xhtml', lang='es')
    c1.content = u'''
    <html>
        <head></head>
        <body>
            <h1>Introducción</h1>
            <p>Este es un libro de prueba para verificar la conversión de EPUB a PDF.</p>
            <p>Contiene texto simple para probar la funcionalidad.</p>
        </body>
    </html>
    '''
    
    c2 = epub.EpubHtml(title='Capítulo 1', file_name='chapter1.xhtml', lang='es')
    c2.content = u'''
    <html>
        <head></head>
        <body>
            <h1>Capítulo 1</h1>
            <p>Este es el primer capítulo del libro de prueba.</p>
            <p>Aquí hay más contenido para verificar que la conversión funcione correctamente.</p>
            <p>El texto debe aparecer en el PDF generado.</p>
        </body>
    </html>
    '''
    
    # Agregar capítulos al libro
    book.add_item(c1)
    book.add_item(c2)
    
    # Definir tabla de contenidos
    book.toc = [
        epub.Link('intro.xhtml', 'Introducción', 'intro'),
        epub.Link('chapter1.xhtml', 'Capítulo 1', 'chapter1')
    ]
    
    # Agregar página de navegación
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Definir el spine
    book.spine = ['nav', c1, c2]
    
    # Crear archivo EPUB
    epub_path = 'test_book.epub'
    epub.write_epub(epub_path, book)
    
    print(f"EPUB de prueba creado: {epub_path}")
    return epub_path

if __name__ == "__main__":
    epub_file = create_test_epub()
    print(f"Archivo EPUB creado exitosamente: {epub_file}")
    print("Ahora puedes probar la conversión usando el endpoint /tools/convert-epub-to-pdf") 