---
id: STORY-001
title: Repo scaffold + four-zone structure
type: chore
---

## Context
Spec: `uptime-monitor-v3-design.html` §4 (the four backend zones) and §3 (stack).
This is the first story of Sprint 0. Nothing exists yet but design docs. The whole
architecture rests on a one-directional dependency boundary between four zones; this
story lays down the physical structure that the CI contracts (STORY-002) will then
police. No business logic — just the skeleton, the package layout, and a runnable
test harness.

## Description
Create the backend Python package under `backend/src/` with the four zones from
dossier §4, plus the finer internal layering inside `core/`:

```
backend/src/
├── core/
│   ├── domain/        # pure data, depends on nothing
│   ├── ports/         # interfaces expressed in domain types
│   └── services/      # logic; calls ports, manipulates domain types
├── adapters/
│   ├── inbound/       # e.g. dynatrace (ingest)
│   ├── outbound/      # e.g. statuspage (publish)
│   └── persistence/   # e.g. neon (repositories)
├── composition/       # the wiring / "main" layer
└── api/               # thin FastAPI HTTP surface
```

Each package gets an `__init__.py` so it is importable as `src.<zone>...` (the exact
module paths the import-linter contracts in STORY-002 reference). Set up the Python
project (`pyproject.toml`) so `src` is the importable top-level package
(`package-dir = {"" = "backend"}`), a `.venv`, and `pytest` as the test runner.
Author the initial `CLAUDE.md` (YourTeam pointer + stack + key commands + tooling
inventory). Keep `config/` reserved at the repo root per dossier §4/§7 (config lives
outside `backend/` to signal that editing it is a topology change) — a `config/`
directory with a short README placeholder is enough for now.

Conventions to honor: Python 3.13, FastAPI/SQLAlchemy/Alembic stack (deps may be
declared in `pyproject.toml` even if a given zone's code arrives in a later story).
Do NOT write any domain/business logic — that's Zone 1 onward.

## Acceptance Criteria
- [ ] AC1: `pytest` runs and exits 0 with zero tests collected (an empty but valid
      harness is acceptable). A trivial `tests/test_smoke.py` asserting the package
      imports is allowed but must genuinely pass.
- [ ] AC2: The four zones exist as importable packages under `backend/src/`
      (`core` with `domain`/`ports`/`services` subpackages, `adapters` with
      `inbound`/`outbound`/`persistence`, `composition`, `api`), each with
      `__init__.py`; `python -c "import src.core, src.adapters, src.composition, src.api"`
      succeeds (run with `backend` importable).
- [ ] AC3: `CLAUDE.md` exists at the repo root and contains: project overview, stack,
      key commands, a tooling inventory, and the YourTeam session-start pointer
      ("read `.scrum/sprint-current.yaml`, resume from board state, honor
      `.scrum/working-agreements.md`").
- [ ] AC4: `pyproject.toml` declares the project and makes `src` importable from
      `backend/`; the dependency toolchain is pinned enough that `pip install -e .`
      (or the documented install command) succeeds in a fresh `.venv`.

## Open Questions
<!-- none — ready -->

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §3/§4; refined to ready for Sprint 0.
- 2026-06-23: implemented (commits 862f44a, 29afbb3, c641664, d9441c2). Spec review PASS
  (all AC MET); quality review APPROVE. DoD gate: `pytest` exit 0. Marked Done.
- 2026-06-23: QUALITY-MINOR (non-blocking note): bare `pytest` currently requires
  `pip install -e ".[dev]"` first; adding `[tool.pytest.ini_options] pythonpath = ["backend"]`
  would make the harness self-contained for a fresh clone / CI without an editable install.
  Candidate tiny chore if it causes friction — STORY-002/003 will surface whether it matters.
