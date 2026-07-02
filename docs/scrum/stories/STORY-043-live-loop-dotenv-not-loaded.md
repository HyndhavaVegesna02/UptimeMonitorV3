---
id: STORY-043
title: Defect — the live loop (and asgi app) never load the .env file; docs claim they do
type: defect
---

## Context / how it surfaced
Found during the STORY-042 AC5 manual end-to-end check (2026-07-02). With the full local stack up
(throwaway DB + `uvicorn src.composition.asgi:app` + `python -m src.composition.run`), the live loop
crashed immediately:

```
src.composition.settings.MissingLiveSecretError: Missing required live secrets:
DYNATRACE_ENV_URL, DYNATRACE_API_TOKEN
```

— even though a gitignored `.env` at the repo root contains all four secrets. Root cause:
`backend/src/composition/settings.py::load_live_secrets` and `::load_settings` read **only
`os.environ`**; there is **no dotenv loading anywhere in `backend/src/`** (`grep -r dotenv` → none).
So the `.env` file is never read. CLAUDE.md claims the opposite in multiple places — e.g. the
STORY-042 "Run the app locally" recipe says *"`python -m src.composition.run` (reads `.env`
secrets)"*, and the "Live-loop secrets" section says secrets are *"read from the environment / a
gitignored `.env` via `load_live_secrets()`"*. Neither is true: the loop only works if the secrets
are already **exported** into the process environment (which is how STORY-016c's live run actually
succeeded). Running strictly per the documented recipe fails.

The rest of AC5 is otherwise GOOD: once the secrets were exported inline, the loop ingested 120 real
observations from the live Dynatrace tenant, and `/components`, `/history`, and `/availability` all
served genuine live data (`/approvals` + `/publications` correctly empty — healthy monitor, nothing
to approve or publish). So this defect is isolated to the `.env`-loading gap between code and docs.

## Acceptance Criteria
- [ ] AC1 (repro fixed): given a repo-root `.env` containing the live secrets and NO secrets exported
      in the shell, `python -m src.composition.run` loads them from `.env` and starts the loop (no
      `MissingLiveSecretError`). A test proves `.env` is loaded at the entrypoint (e.g. point the
      loader at a temp `.env` and assert the secrets resolve without them being in `os.environ`).
- [ ] AC2: the same `.env` loading applies to the API server entrypoint (`composition/asgi.py`) so
      `DATABASE_URL` (and any other config) can also come from `.env` — the documented stack works
      end to end from a `.env` alone.
- [ ] AC3: env-var precedence is preserved — an already-exported variable is NOT overridden by `.env`
      (so tests and production, which set real env vars, are unaffected). Tested.
- [ ] AC4: does not run in tests/CI unintentionally — loading is at the process entrypoints
      (`run.py::main`, `asgi.py`), NOT inside `load_settings`/`load_live_secrets` (which tests call
      directly with explicit env). The six backend DoD gates stay green.
- [ ] AC5: CLAUDE.md is accurate — the "Run the app locally" recipe and the "Live-loop secrets"
      section match the shipped behavior (either "reads `.env`" is now true, or the recipe says
      "export the secrets first" — AC1 makes the former true).

## Open Questions (resolve at refinement/planning)
- Dependency: `python-dotenv` is the obvious mechanism. It is imported at runtime by `run.py`, so it
  must be a RUNTIME dep (not dev-only) or the import must be guarded — decide which. (`load_dotenv()`
  is a no-op when no `.env` exists, so it is safe on Railway where the platform sets real env vars.)

## History
- 2026-07-02: filed from the STORY-042 AC5 live check — the documented `.env`-based run path does not
  work because nothing loads `.env`. Estimate 2 (defect: add entrypoint dotenv load + dep + test +
  doc fix).
