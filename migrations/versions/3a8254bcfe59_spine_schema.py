"""spine schema

The full eleven-table spine (dossier §9), in one reversible migration on top
of the empty `eda70ac11454` baseline. Three groups:

  - topology (seeded later from Git config; idempotent upsert is a later
    story): `apps` (carries `config jsonb not null`), `signals`, `components`.
  - signals (runtime, append-only): `observations`, `problem_signals`,
    `watermarks`, `rejected_observations`.
  - workflow (runtime, V2-proven shapes): `status_proposals`,
    `approval_events`, `publications`, `maintenance_windows`.

Conventions used throughout:
  - Every timestamp column is `timestamptz` (dossier §9 Postgres upgrade over
    V2's SQLite) — never bare `timestamp`.
  - `apps.config`, `observations.source`, and `rejected_observations.payload`
    are `jsonb`. `apps.config` is NOT NULL (seeded topology, dossier §9 /
    Tier-2 item 6).
  - Every FK declares an explicit `ON DELETE` behavior. FKs that reference
    seeded topology (`apps`, `signals`, `components`) use `ON DELETE
    RESTRICT` — seeded topology is never silently cascaded away by a runtime
    row being inserted against it. FKs between runtime/workflow rows that are
    genuinely a parent/child lifecycle (`status_proposals` -> `approval_events`
    / `publications`) use `ON DELETE CASCADE`, since an approval event or
    publication record has no meaning once its owning proposal is gone — that
    is still an explicit, deliberate choice, not a default.
  - `health` / `status` / proposal `state` are stored as `text` with a CHECK
    constraint mirroring the closed enums (`Health`, `ComponentStatus`) rather
    than a Postgres ENUM type, so the core's Python enums stay the single
    source of truth and changing a member never requires an `ALTER TYPE`.

The "active" predicate for the partial-unique proposal index (dossier §9 ->
§11, AC3) is `state = 'open'`: a proposal is open from creation until a human
or the reconciliation rule resolves it (approved / rejected / superseded /
obsoleted), at which point `resolved_at` and the terminal `state` are set.
Exactly one open proposal can exist per `component_id` at a time.

Revision ID: 3a8254bcfe59
Revises: eda70ac11454
Create Date: 2026-06-24 13:21:59.601511

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3a8254bcfe59"
down_revision: Union[str, Sequence[str], None] = "eda70ac11454"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the full eleven-table spine, in topology -> signals -> workflow order."""

    # ---------------------------------------------------------------
    # Topology group — seeded from Git config at boot; idempotent upsert
    # is a later story. Created first because everything else FKs into it.
    # ---------------------------------------------------------------

    op.create_table(
        "apps",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "signals",
        sa.Column("signal_key", sa.Text(), primary_key=True),
        sa.Column(
            "app_id",
            sa.Text(),
            sa.ForeignKey("apps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_signals_app_id", "signals", ["app_id"])

    op.create_table(
        "components",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "app_id",
            sa.Text(),
            sa.ForeignKey("apps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="operational",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('operational', 'degraded', 'partial_outage', 'major_outage')",
            name="ck_components_status",
        ),
    )
    op.create_index("ix_components_app_id", "components", ["app_id"])

    # ---------------------------------------------------------------
    # Signals group — runtime, append-only.
    # ---------------------------------------------------------------

    op.create_table(
        "observations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "signal_key",
            sa.Text(),
            sa.ForeignKey("signals.signal_key", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("health", sa.Text(), nullable=False),
        sa.Column("source_event_id", sa.Text(), nullable=False),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("raw_ref", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "health IN ('up', 'down', 'degraded')",
            name="ck_observations_health",
        ),
    )
    op.create_unique_constraint(
        "uq_observations_source_event_id",
        "observations",
        ["source_event_id"],
    )
    op.create_index(
        "ix_observations_signal_key_observed_at",
        "observations",
        ["signal_key", "observed_at"],
    )

    op.create_table(
        "problem_signals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "signal_key",
            sa.Text(),
            sa.ForeignKey("signals.signal_key", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_problem_signals_signal_key", "problem_signals", ["signal_key"])

    op.create_table(
        "watermarks",
        sa.Column(
            "signal_key",
            sa.Text(),
            sa.ForeignKey("signals.signal_key", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("watermark", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "rejected_observations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("signal_key", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rejected_at", sa.TIMESTAMP(timezone=True), nullable=False),
        # Deliberately NO FK to `signals`: a rejected observation may carry a
        # signal_key that does not (or does not yet) exist in seeded topology
        # — that is often exactly *why* it was rejected. Quarantine must not
        # itself be rejectable by a missing-FK error.
    )
    op.create_index(
        "ix_rejected_observations_signal_key",
        "rejected_observations",
        ["signal_key"],
    )

    # ---------------------------------------------------------------
    # Workflow group — runtime, V2-proven shapes.
    # ---------------------------------------------------------------

    op.create_table(
        "status_proposals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "component_id",
            sa.Text(),
            sa.ForeignKey("components.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="open"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "proposed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "to_status IN ('operational', 'degraded', 'partial_outage', 'major_outage')",
            name="ck_status_proposals_to_status",
        ),
        sa.CheckConstraint(
            "from_status IS NULL OR from_status IN "
            "('operational', 'degraded', 'partial_outage', 'major_outage')",
            name="ck_status_proposals_from_status",
        ),
        sa.CheckConstraint(
            "state IN ('open', 'approved', 'rejected', 'superseded', 'obsoleted')",
            name="ck_status_proposals_state",
        ),
    )
    # Partial UNIQUE index (dossier §9 -> §11, AC3): at most one OPEN proposal
    # per component. "Active" == state = 'open' — a proposal is open from
    # creation until approved / rejected / superseded / obsoleted.
    op.create_index(
        "uq_status_proposals_active_component",
        "status_proposals",
        ["component_id"],
        unique=True,
        postgresql_where=sa.text("state = 'open'"),
    )
    op.create_index(
        "ix_status_proposals_component_id",
        "status_proposals",
        ["component_id"],
    )

    op.create_table(
        "approval_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "proposal_id",
            sa.BigInteger(),
            sa.ForeignKey("status_proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action IN ('approved', 'rejected')",
            name="ck_approval_events_action",
        ),
    )
    op.create_index(
        "ix_approval_events_proposal_id", "approval_events", ["proposal_id"]
    )

    op.create_table(
        "publications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "component_id",
            sa.Text(),
            sa.ForeignKey("components.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "proposal_id",
            sa.BigInteger(),
            sa.ForeignKey("status_proposals.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('operational', 'degraded', 'partial_outage', 'major_outage')",
            name="ck_publications_status",
        ),
    )
    op.create_index("ix_publications_component_id", "publications", ["component_id"])

    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "component_id",
            sa.Text(),
            sa.ForeignKey("components.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_maintenance_windows_component_id",
        "maintenance_windows",
        ["component_id"],
    )


def downgrade() -> None:
    """Drop every spine object cleanly, in reverse dependency order."""

    op.drop_index(
        "ix_maintenance_windows_component_id", table_name="maintenance_windows"
    )
    op.drop_table("maintenance_windows")

    op.drop_index("ix_publications_component_id", table_name="publications")
    op.drop_table("publications")

    op.drop_index("ix_approval_events_proposal_id", table_name="approval_events")
    op.drop_table("approval_events")

    op.drop_index("ix_status_proposals_component_id", table_name="status_proposals")
    op.drop_index("uq_status_proposals_active_component", table_name="status_proposals")
    op.drop_table("status_proposals")

    op.drop_index(
        "ix_rejected_observations_signal_key", table_name="rejected_observations"
    )
    op.drop_table("rejected_observations")

    op.drop_table("watermarks")

    op.drop_index("ix_problem_signals_signal_key", table_name="problem_signals")
    op.drop_table("problem_signals")

    op.drop_index("ix_observations_signal_key_observed_at", table_name="observations")
    op.drop_constraint(
        "uq_observations_source_event_id", "observations", type_="unique"
    )
    op.drop_table("observations")

    op.drop_index("ix_components_app_id", table_name="components")
    op.drop_table("components")

    op.drop_index("ix_signals_app_id", table_name="signals")
    op.drop_table("signals")

    op.drop_table("apps")
