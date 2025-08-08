"""recreate books table with nullable drive_file_id

Revision ID: recreate_books_table_nullable
Revises: add_synced_to_drive_column
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'recreate_books_table_nullable'
down_revision = 'add_synced_to_drive_column'
branch_labels = None
depends_on = None


def upgrade():
    # Crear nueva tabla con drive_file_id nullable
    op.create_table('books_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('cover_image_url', sa.String(), nullable=True),
        sa.Column('drive_file_id', sa.String(), nullable=True),  # Ahora nullable
        sa.Column('drive_web_link', sa.String(), nullable=True),
        sa.Column('drive_letter_folder', sa.String(), nullable=True),
        sa.Column('drive_filename', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('synced_to_drive', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copiar datos existentes
    op.execute("""
        INSERT INTO books_new (id, title, author, category, cover_image_url, 
                              drive_file_id, drive_web_link, drive_letter_folder, 
                              drive_filename, file_path, synced_to_drive)
        SELECT id, title, author, category, cover_image_url, 
               drive_file_id, drive_web_link, drive_letter_folder, 
               drive_filename, file_path, synced_to_drive
        FROM books
    """)
    
    # Eliminar tabla antigua
    op.drop_table('books')
    
    # Renombrar nueva tabla
    op.rename_table('books_new', 'books')


def downgrade():
    # Crear tabla antigua con drive_file_id NOT NULL
    op.create_table('books_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('cover_image_url', sa.String(), nullable=True),
        sa.Column('drive_file_id', sa.String(), nullable=False),  # NOT NULL
        sa.Column('drive_web_link', sa.String(), nullable=True),
        sa.Column('drive_letter_folder', sa.String(), nullable=True),
        sa.Column('drive_filename', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('synced_to_drive', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copiar solo registros con drive_file_id no nulo
    op.execute("""
        INSERT INTO books_old (id, title, author, category, cover_image_url, 
                              drive_file_id, drive_web_link, drive_letter_folder, 
                              drive_filename, file_path, synced_to_drive)
        SELECT id, title, author, category, cover_image_url, 
               drive_file_id, drive_web_link, drive_letter_folder, 
               drive_filename, file_path, synced_to_drive
        FROM books
        WHERE drive_file_id IS NOT NULL
    """)
    
    # Eliminar tabla nueva
    op.drop_table('books')
    
    # Renombrar tabla antigua
    op.rename_table('books_old', 'books') 