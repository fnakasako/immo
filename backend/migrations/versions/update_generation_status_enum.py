"""Update generation status enum

Revision ID: update_generation_status_enum
Revises: be9b7699b828
Create Date: 2025-03-11 02:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_generation_status_enum'
down_revision = 'be9b7699b828'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update the generationstatus enum to include all values
    op.execute("ALTER TYPE generationstatus ADD VALUE IF NOT EXISTS 'OUTLINE_COMPLETED'")
    op.execute("ALTER TYPE generationstatus ADD VALUE IF NOT EXISTS 'SECTIONS_COMPLETED'")
    op.execute("ALTER TYPE generationstatus ADD VALUE IF NOT EXISTS 'PROCESSING_SCENES'")
    op.execute("ALTER TYPE generationstatus ADD VALUE IF NOT EXISTS 'SCENES_COMPLETED'")
    op.execute("ALTER TYPE generationstatus ADD VALUE IF NOT EXISTS 'PROCESSING_PROSE'")


def downgrade() -> None:
    # Cannot remove enum values in PostgreSQL
    pass
