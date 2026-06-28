# Sprint 19 — Review

**Goal:** Publications feature module — a `PublicationRepository` over the existing `publications`
table, a `RecordingPublisher` decorator that records each successful publish, and
`GET /api/v1/publications`. The last pure-backend feature before the credential-gated live demo.

**Branch:** `sprint-19` (from `sprint-19-start` @ `e95bc6b`) · **HEAD:** `b80552d` (+ compile-pass commit)
**Committed:** 5 pts · **Story:** STORY-037 — Done.

## Mechanical DoD gate (orchestrator-verified, committed tree)

| Command | Result |
| --- | --- |
| `pytest` | **404 passed** |
| `lint-imports` | **5 kept, 0 broken** (`publications` joined `api-feature-independence`) |
| `check_fk_direction.py` | 11 FKs, 0 violations |
| `alembic upgrade head` | no-op (no migration — `publications` table pre-existed) |
| `ruff check` / `format --check` | clean (146 files) |

Implemented by a **Sonnet implementer subagent** (PO asked to finish it in-sprint), then verified +
reviewed by the orchestrator.

---

## STORY-037 — Publications feature module (5 pts)

- `core/domain/publication.py::Publication` (frozen, UTC-validated `published_at`); `PublicationRepository`
  (`record`, `list_recent`) + Postgres adapter + fake; `composition/publish_helper.py::RecordingPublisher`
  (records on a successful publish, using the clock; a raising delegate records nothing + propagates;
  composes inside `BestEffortPublisher`); `api/v1/publications` five-file read feature
  (`GET /api/v1/publications`, most-recent-first). No migration; records successes only (no error column).

| AC | Verdict |
| --- | --- |
| AC1 repository + fake/adapter parity | MET |
| AC2 RecordingPublisher (records on success; nothing on failure; composes w/ BestEffort) | MET |
| AC3 GET endpoint (most-recent-first, empty→[], DTO distinct, five-file shape) | MET |
| AC4 full gate + blast radius | MET |

- **Opus spec reviewer: PASS** — all four AC MET; each "tested" clause traced to drive its named path
  (record-on-success asserts the clock time; failure path asserts nothing recorded + error propagates;
  GET ordering asserted with ≥2 rows).
- **Opus quality reviewer: APPROVE** — 0 critical / 0 major. `RecordingPublisher` semantics correct
  (publish-first, record-only-on-success, uses the clock, doesn't swallow); fake/adapter parity; SQL
  parameterized; DB-test isolation confirmed (ran the suite twice on the reused DB, green both times).

**First pass — no fix loop.** The two minors are non-actionable (`assert row is not None` mirrors the
sibling adapters; a lazy import matches the file's DB-branch convention).

## Orchestrator note
The implementer left a ruff-format import-wrap uncommitted, so the committed HEAD would have failed
`ruff format --check` (only the dirty tree passed). The orchestrator committed it (`b80552d`) so the
committed tree is genuinely gate-green. Worth flagging at the retro (an external implementer leaving an
uncommitted format fix means committed-HEAD ≠ the gate-green tree).

## Outcome
**The entire backend is now complete** — ingest → pipeline → proposals → approve/reject → (best-effort,
recorded) publish, with a seeded spine and the full six-tab read/write API. Remaining: the
credential-gated **STORY-016** (live demo — Dynatrace Executor + Statuspage wiring incl.
`BestEffortPublisher` + `RecordingPublisher`) and **STORY-017** (deploy); then **STORY-015** (frontend).

## PO verdict requested
**accept** (merge to main) or **reject**. Both reviewers passed first pass; you asked to finish it
in-sprint.
