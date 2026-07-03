"""add signals.interval_seconds

STORY-044 (D1): `signals.interval_seconds` is a NULLABLE Integer column,
backfilled by the boot seed (`composition/seed.py::seed_topology`) from
`composition/config.py::SignalConfig.interval_seconds`. Nullable because a
migration cannot read `config/` (config is composition's job) and must not
invent a default — the seed is the backfill, so the first boot after upgrade
populates every configured signal. No FK, no spine-direction change.

Revision ID: 5ed254a8daab
Revises: eec78d2e8cbe
Create Date: 2026-07-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ed254a8daab"
down_revision: Union[str, Sequence[str], None] = "eec78d2e8cbe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "signals",
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("signals", "interval_seconds")
