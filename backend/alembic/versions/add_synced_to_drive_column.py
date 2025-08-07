"""Add synced_to_drive column to books table

Revision ID: add_synced_to_drive_column
Revises: 2b3c4d5e6f7g
Create Date: 2024-08-04 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_synced_to_drive_column'
down_revision = '2b3c4d5e6f7g'
branch_labels = None
depends_on = None

def upgrade():
    # Agregar columna synced_to_drive a la tabla books
    op.add_column('books', sa.Column('synced_to_drive', sa.Boolean(), nullable=True, default=False))

def downgrade():
    # Remover columna synced_to_drive de la tabla books
    op.drop_column('books', 'synced_to_drive') 