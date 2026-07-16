# Sprint 49 — Review

**Goal:** Complete the AWS cutover — run on DynamoDB, containerized, one console session from AWS.
**Mode:** external. **Committed:** 10 pts (087:3 + 092:2 + 088:5).
**Delivery HEAD:** `5b4ee36` → **review-tail fixes → final HEAD `8a18e08`.**

## Verification floor (orchestrator, external mode)
- **Full amended 8-command DoD gate re-run on final HEAD `8a18e08` with DynamoDB Local up — ALL GREEN.**
  `pytest` **521 passed / 0 skipped** (persistence suite executed), lint-imports 8/8 contracts kept,
  ruff check/format clean, `cfn-lint infra/stack.yaml` exit 0, frontend `npm test` 363 passed /
  build / lint all green. (The delivery's self-reported `evidence.yaml` was treated as a
  to-verify list, not evidence — this is the record.)
- **Spec + quality review PER STORY** (external-mode requirement, regardless of points).
- **Reality gates run live** (see each story).

## Per-story outcome

### STORY-087 — Composition cutover to DynamoDB (3 pts)
The substance was correct at delivery: `create_app`/`build_live_loop`/`main` wire the DynamoDB
adapters with the exact table split (observation→observations table; everything else, incl.
rejected→control table), zero Postgres/SQLAlchemy/psycopg residue under `backend/src`, all nine
Postgres adapters + `composition/seed.py` + the Alembic tree + `dev_db.py`/`check_fk_direction.py`
deleted, the two kept Dynamo parity-test files surgically de-coupled (no coverage loss), and the
DoD amendment landed (two Postgres gates retired). **AC1/AC3 MET at delivery.**
- **Spec FAIL → fixed:** AC2 deletion reasons weren't recorded (→ story History added), AC4 e2e
  evidence absent (→ reality gate run + recorded), AC5 wiki/CLAUDE.md not truly resolved.
- **Quality FIX_REQUIRED → fixed:** MAJOR — `asgi.py` docstring still described the deleted
  SQLAlchemy engine / `DATABASE_URL` on a live entrypoint (rewritten); MAJOR — `verified_sha`
  bulk-laundered to a 40-char sha across 12 wiki articles (de-laundered per-article).
- **Reality gate (read/serve path — PASS, live vs real DynamoDB Local):** API boots on DynamoDB,
  boot seed populates the control table, all six-tab endpoints serve (`/components` returns the
  seeded `http-check`), `create_tables.py` runs with no `DATABASE_URL`. **Live-loop ingest +
  watermark-advance + mutation round-trip requires live Dynatrace/Statuspage creds (unset
  in-session) → carved to STORY-089, not silently deferred.**
- **Wiki:** `migrations-and-db.md` archived with a real tombstone (moved to `wiki/archive/`,
  `archived_sprint`/`archived_reason` + banner); `architecture-boundary.md` updated for FK-direction
  retirement (dropped from code_refs; import boundary is now the sole CI floor); new
  `deployment-and-infra.md`. `yt_wiki.py` exit 0.

### STORY-092 — Containerize both processes (2 pts)
Single `Dockerfile` (`python:3.13-slim`, runtime deps only, default CMD = API, loop via override),
no Postgres layer. **AC1/AC2/AC5 MET at delivery.**
- **Spec FAIL → fixed:** AC3 `.dockerignore` was missing `backend/tests/` + `.claude/`, so
  `COPY backend` shipped the test suite into the image (added the excludes + nested `__pycache__`).
- **Quality FIX_REQUIRED → fixed:** same `.dockerignore` MAJOR; MAJOR — the CLAUDE.md local Docker
  recipe put DynamoDB Local and the API both on host port 8000 (moved DynamoDB Local to 8001).
- **Reality gate (PASS):** `docker build` exit 0; container import smoke `import
  src.composition.asgi; import src.composition.run` → "IMPORT SMOKE OK" exit 0.

### STORY-088 — CloudFormation single-stack + console runbook (5 pts)
- **Quality APPROVE (0 critical / 0 major):** IAM scoped to the two table ARNs **+ the `/index/gsi1`
  ARN** + the two secret ARNs (not `*`); SGs locked down (ALB←CloudFront prefix list, API 8000←ALB
  only, loop no ingress); CloudFront `/api/*` all-methods/caching-disabled + the extensionless-rewrite
  function on the default behavior only; loop-singleton `MinimumHealthyPercent:0/MaximumPercent:100`
  on the loop service; `DeletionPolicy: Retain` on both tables + S3; clean secrets hygiene (names/ARNs
  only). Template schema matches `create_tables.py`. **AC1/AC2/AC3/AC5/AC6 MET.**
- **Spec FAIL → fixed:** AC4 — the runbook listed only the 4 Secrets-Manager-backed names and omitted
  the 3 plain env vars (`AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`) per service
  (added), plus a premature "restart services" step reordered after the image push.
- **Reality gate:** vendor-path probe = `cfn-lint` clean + resource-by-resource trace vs the approved
  Context list. Live AWS deploy is STORY-089 (PO-driven, out of scope).

## Deferred minors → proposed follow-up chore (STORY-093, accept-with-follow-up)
Non-root container `USER` + dead `ENV PORT` + Docker layer-cache ordering; `APIService`
`HealthCheckGracePeriodSeconds`; a zero-assertion `test_main_resource_lifecycle_success`; the
plan step-4 no-Postgres guard test; a `monkeypatch.setenv` cleanup. All non-blocking.

## Ask of the PO
Accept/reject each story. Recommendation: **accept all three** (verified floor green, reality gates
run, review-tail applied) **+ approve follow-up chore STORY-093** for the deferred minors. On accept,
the whole `sprint-49` branch merges to main and wiki `verified_sha`s re-stamp to the merge commit.
