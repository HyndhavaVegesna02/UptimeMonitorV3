"""baseline

The empty baseline revision: it establishes the migration chain (alembic_version
gets a row) but creates NO tables. The spine schema arrives in STORY-006. This
exists from day one so migrations are real and versioned — never create_all
(dossier §4). Reversible by design: downgrade is the no-op inverse of upgrade.

Revision ID: eda70ac11454
Revises:
Create Date: 2026-06-23 20:00:14.451413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eda70ac11454'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline — no schema objects yet (spine arrives in STORY-006).

    Intentionally empty: this revision only anchors the migration chain. NEVER
    use create_all here — every table arrives via an explicit migration.
    """
    # No-op: the baseline creates no tables.
    pass


def downgrade() -> None:
    """Reverse of the baseline — also a no-op (nothing was created)."""
    # No-op: there is nothing to drop.
    pass
