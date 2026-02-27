"""add scheduled publish

Revision ID: a3f7c9d12b01
Revises: 61f9238ebc48
Create Date: 2026-02-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f7c9d12b01'
down_revision: Union[str, None] = '61f9238ebc48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'SCHEDULED' value to articlestatus enum (uppercase to match existing DRAFT, PUBLISHED)
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'SCHEDULED'")

    # Add scheduled_publish_at column
    op.add_column('articles', sa.Column('scheduled_publish_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('articles', 'scheduled_publish_at')
    # PostgreSQL does not support removing enum values - leaving 'scheduled' in place
