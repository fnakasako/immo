"""Add simplified status enums

Revision ID: add_simplified_status_enums
Revises: update_generation_status_enum
Create Date: 2025-03-12 20:07:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_simplified_status_enums'
down_revision = 'update_generation_status_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new enum types
    op.execute("CREATE TYPE contentstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")
    
    # Add the new status columns with default values
    op.add_column('content_generations', sa.Column('new_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='contentstatus'), nullable=True))
    op.add_column('sections', sa.Column('new_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='contentstatus'), nullable=True))
    op.add_column('scenes', sa.Column('new_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='contentstatus'), nullable=True))
    
    # Update the new status columns based on the old status values
    # For content_generations
    op.execute("""
    UPDATE content_generations SET new_status = 
        CASE 
            WHEN status = 'PENDING' THEN 'PENDING'::contentstatus
            WHEN status = 'FAILED' THEN 'FAILED'::contentstatus
            WHEN status = 'COMPLETED' THEN 'COMPLETED'::contentstatus
            ELSE 'PROCESSING'::contentstatus
        END
    """)
    
    # For sections
    op.execute("""
    UPDATE sections SET new_status = 
        CASE 
            WHEN status = 'PENDING' THEN 'PENDING'::contentstatus
            WHEN status = 'FAILED' THEN 'FAILED'::contentstatus
            WHEN status = 'COMPLETED' THEN 'COMPLETED'::contentstatus
            ELSE 'PROCESSING'::contentstatus
        END
    """)
    
    # For scenes
    op.execute("""
    UPDATE scenes SET new_status = 
        CASE 
            WHEN status = 'PENDING' THEN 'PENDING'::contentstatus
            WHEN status = 'FAILED' THEN 'FAILED'::contentstatus
            WHEN status = 'COMPLETED' THEN 'COMPLETED'::contentstatus
            ELSE 'PROCESSING'::contentstatus
        END
    """)
    
    # Make the new columns not nullable
    op.alter_column('content_generations', 'new_status', nullable=False)
    op.alter_column('sections', 'new_status', nullable=False)
    op.alter_column('scenes', 'new_status', nullable=False)
    
    # Note: We're keeping the old status columns for backward compatibility
    # In a future migration, we can rename the columns and drop the old enums


def downgrade() -> None:
    # Drop the new status columns
    op.drop_column('content_generations', 'new_status')
    op.drop_column('sections', 'new_status')
    op.drop_column('scenes', 'new_status')
    
    # Drop the new enum type
    op.execute("DROP TYPE contentstatus")
