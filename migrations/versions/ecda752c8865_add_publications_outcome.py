"""add publications outcome

STORY-072 — record every approve publish ATTEMPT, independent of whether the
Statuspage publish itself succeeds (dossier §9, §12/T1.1, §17). Root cause
(2026-07-08): `RecordingPublisher` recorded successes only, so a real
Statuspage 401 recorded nothing and the Publications tab stayed empty even
though `approve` returned 200. The PO decision is to always record the
attempt with a `succeeded`/`failed` outcome; the Statuspage publish itself
stays best-effort (out of scope here).

`outcome` is DISTINCT from the existing `status` column — `status` is the
health status that was (attempted to be) published; `outcome` is whether the
Statuspage call itself succeeded or raised. Added nullable first, backfilled
to `'succeeded'` (every existing row was recorded under the old
success-only path, so that's the only truthful backfill value), then made
NOT NULL — mirrors the CHECK-constrained-text convention used for `status`
on this same table (dossier §9 spine migration).

Revision ID: ecda752c8865
Revises: 09e9aa2cee32
Create Date: 2026-07-08 16:40:39.739293

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ecda752c8865"
down_revision: Union[str, Sequence[str], None] = "09e9aa2cee32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PUBLICATIONS = sa.table("publications", sa.column("outcome", sa.Text()))


def upgrade() -> None:
    """Add nullable `outcome`, backfill existing rows, then enforce NOT NULL + CHECK."""
    op.add_column("publications", sa.Column("outcome", sa.Text(), nullable=True))

    op.execute(_PUBLICATIONS.update().values(outcome="succeeded"))

    op.alter_column("publications", "outcome", nullable=False)
    op.create_check_constraint(
        "ck_publications_outcome",
        "publications",
        "outcome IN ('succeeded', 'failed')",
    )


def downgrade() -> None:
    """Drop the CHECK constraint and the `outcome` column."""
    op.drop_constraint("ck_publications_outcome", "publications", type_="check")
    op.drop_column("publications", "outcome")
