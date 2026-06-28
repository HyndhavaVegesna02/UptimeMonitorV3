"""add signals.component_id

Revision ID: eec78d2e8cbe
Revises: 3a8254bcfe59
Create Date: 2026-06-28 23:28:20.472805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eec78d2e8cbe'
down_revision: Union[str, Sequence[str], None] = '3a8254bcfe59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "signals",
        sa.Column(
            "component_id",
            sa.Text(),
            sa.ForeignKey("components.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("ix_signals_component_id", "signals", ["component_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_signals_component_id", table_name="signals")
    op.drop_column("signals", "component_id")
