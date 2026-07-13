"""add maintenance window title

STORY-065 — add optional title field to maintenance windows (dossier §9, §10, §17).

Revision ID: b52c8865a2c1
Revises: a2c1d89efcea
Create Date: 2026-07-13 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b52c8865a2c1"
down_revision: Union[str, Sequence[str], None] = "a2c1d89efcea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable `maintenance_windows.title` (Text, nullable=True)."""
    op.add_column(
        "maintenance_windows",
        sa.Column("title", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Drop `maintenance_windows.title`."""
    op.drop_column("maintenance_windows", "title")
