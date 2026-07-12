"""add observations response_status_code

STORY-064 — capture the HTTP response status code alongside each observation
(dossier §5, §17). The live-Grail probe (2026-07-12, monitor
`HTTP_CHECK-38B092E93932C002`) confirmed every sampled `http_monitor_execution`
row carries `result.statistics.response_status_code`; the normalizer parses it
to an optional int (`_assembly.py::assemble_observation`) and it was being
dropped entirely before this migration. Nullable, no default, no backfill: a
row is either normalized post-STORY-064 (an int or a genuine `None` for a
missing/unparsable value) or predates this column (also `NULL` — no data to
invent). No CHECK constraint — an HTTP status code is not a closed vocabulary
like `health`/`status`.

Revision ID: a2c1d89efcea
Revises: ecda752c8865
Create Date: 2026-07-12 21:57:21.842697

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2c1d89efcea"
down_revision: Union[str, Sequence[str], None] = "ecda752c8865"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable `observations.response_status_code` (Integer, no default)."""
    op.add_column(
        "observations",
        sa.Column("response_status_code", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Drop `observations.response_status_code`."""
    op.drop_column("observations", "response_status_code")
