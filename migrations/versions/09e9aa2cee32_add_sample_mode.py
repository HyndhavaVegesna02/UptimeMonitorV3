"""add sample_mode

STORY-048 (D1) — a TEMPORARY feature (PO directive, 2026-07-03): a
dedicated, droppable single-row table for the sample-mode flag (the on-demand
outage simulator). NO FK in either direction (so `check_fk_direction.py`'s
SPINE allowlist is untouched) and NO existing table is modified. The
`CHECK (id)` constraint on the boolean primary key pins the table to at most
one row, matching D1's single-row-flag design.

Never-set -> `False` is enforced by the PORT (`SampleModeRepository.is_enabled`),
NOT by seeding a default row here — so `upgrade()` creates an EMPTY table.

Paired removal expectation (see `docs/scrum/wiki/sample-mode.md`'s REMOVAL
inventory): when sample-mode is deleted, a follow-up migration chains from
whatever is head at that time and DROPs this table; this migration's own
`downgrade()` already does exactly that for local/CI reversibility testing.

Revision ID: 09e9aa2cee32
Revises: 5ed254a8daab
Create Date: 2026-07-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "09e9aa2cee32"
down_revision: Union[str, Sequence[str], None] = "5ed254a8daab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sample_mode",
        sa.Column("id", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("id", name="ck_sample_mode_single_row"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("sample_mode")
