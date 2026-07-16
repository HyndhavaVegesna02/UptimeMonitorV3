---
id: STORY-092
title: Containerize both processes — single Dockerfile, CMD override per role
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). STORY-088's approved topology assumes a
single container image in ECR that "serves both processes via CMD override" — the API
(`uvicorn src.composition.asgi:app`) and the live loop (`python -m src.composition.run`)
run from one image, each ECS task definition overriding the command. That Dockerfile
does not exist yet (the repo has never been containerized). This story authors it.

Split out of STORY-088 at sprint-49 planning (PO directive 2026-07-16): the missing
Dockerfile is real, previously-unscoped work, so it gets its own story with its own AC
rather than being smuggled into 088's estimate. Ordered AFTER STORY-087 so the image is
built against the DynamoDB-only runtime — no `psycopg`/SQLAlchemy layer, no
`DATABASE_URL` requirement to start.

## Description
Author a single repo-root `Dockerfile` (Python 3.13 slim base) that installs the backend
`src` package and its runtime dependencies and can run either process by command
override, plus a `.dockerignore` that keeps the build context lean. Smoke-verify the
image builds and both entrypoints import inside it. Document the two invocations.

## Acceptance Criteria
- [ ] AC1 (single image, default = API): a repo-root `Dockerfile` on a `python:3.13-slim`
      base installs the project via `pip install .` (runtime deps only — no `[dev]`
      extra) and sets a default `CMD` running the API:
      `uvicorn src.composition.asgi:app --host 0.0.0.0 --port 8000`. The image contains
      the `src` package and `config/`; it does NOT install SQLAlchemy/Alembic/psycopg
      (those left `pyproject.toml` in STORY-087).
- [ ] AC2 (loop via override): running the same image with the command overridden to
      `python -m src.composition.run` starts the live loop. The runbook (STORY-088) and
      the ECS loop task definition use exactly this override; the Dockerfile hard-codes
      no loop-specific command.
- [ ] AC3 (lean context): a `.dockerignore` excludes `.venv/`, `.git/`,
      `frontend/node_modules/`, `frontend/dist/`, `**/__pycache__/`, `backend/tests/`,
      `.scrum/`, `docs/`, and `.claude/` so they never enter the build context.
- [ ] AC4 (build + import smoke, evidence recorded): `docker build -t uptime-monitor .`
      succeeds, and `docker run --rm --entrypoint python uptime-monitor -c "import
      src.composition.asgi; import src.composition.run"` exits 0 (both entrypoints import
      with no Postgres dependency present). The build+smoke output is recorded as the
      story's reality-gate evidence.
- [ ] AC5 (docs): CLAUDE.md's tooling inventory / Key commands note the Dockerfile and
      the two invocations (default API CMD + loop override); wiki blast radius resolved
      (deploy/runtime articles, if any code_refs overlap).

## Open Questions
None (resolved at planning: base image `python:3.13-slim`; default CMD = API, loop by
override; `pip install .` runtime-only; PO-approved 2026-07-16).

## History
- 2026-07-16: split out of STORY-088 at sprint-49 planning; drafted with AC + 2-point
  estimate for PO approval in the same planning touchpoint.
