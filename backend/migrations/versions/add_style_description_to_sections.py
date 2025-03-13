"""Add style_description column to sections table

Revision ID: add_style_description_to_sections
Revises: update_generation_status_enum
Create Date: 2025-03-12 16:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_style_desc'
down_revision = 'update_generation_status_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add style_description column to sections table
    op.add_column('sections', sa.Column('style_description', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove style_description column from sections table
    op.drop_column('sections', 'style_description')