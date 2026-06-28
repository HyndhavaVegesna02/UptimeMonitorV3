# Sprint 20 — Plan

**Goal.** Make the first thread LIVE. Build the two real HTTP `Executor`s (Dynatrace Grail DQL +
Statuspage PATCH) that were left as injected seams, add their credentials to `settings.py`, carry the
Statuspage component mapping in config, thread orchestration through `run_periodic`, and assemble a
composition entrypoint that runs the live loop with
`BestEffortPublisher(RecordingPublisher(StatuspagePublisher))`. Everything is **gate-green via recorded
fixtures** — no live call in any test. The live observation against the real SaaS is a **manual
post-merge smoke** (T5 runbook), not a gated AC.

**Single story: STORY-016 (5 pts)** — top of the velocity range (last-3 mean 5.0). Pipeline:
`gate + Opus spec & quality reviewers` (5 pts ⇒ both reviewers per the 2026-01-01 default).

## Baseline
- Branch: `sprint-20`, cut from `main` @ `994b637`.
- Topology prep already committed @ `58b4072` (live `httpcheck` config, sockshop dropped, two
  real-config tests repointed). Cheap gates green there (ruff clean; lint-imports 5/0; 404 passed).
- `start_tag`: `sprint-20-start` (set at lock, after the board/plan commit).
- DB-gated gates run via the shared throwaway-DB harness (`scripts/dev_db.py` / `migrated_db` fixture).

## Architecture the wiring lands in (already built — do NOT re-derive)
- `adapters/inbound/dynatrace/query.py::Executor = Callable[[str], list[dict]]` — the DQL seam.
  `build_dql_query(*, native_id, watermark, overlap)` is pure and DONE; the normalizers
  (`http_normalizer`, `_assembly.assemble_observation`) consume the flat row-dict shape below.
- `adapters/outbound/statuspage::Executor = Callable[[method, url, headers, json], dict]` — the HTTP seam.
  `StatuspagePublisher.publish` is DONE; it calls `self._executor("PATCH", url, headers, json_body)`.
- `composition/publish_helper.py` — `BestEffortPublisher`, `RecordingPublisher` are DONE.
- `composition/orchestrate.py::orchestrate_signal(*, signal_key, config, observation_repo,
  maintenance_repo, component_repo, decide_service, clock)` is DONE.
- `core/services/decide.py::DecideService(*, proposal_repo, publisher)` is DONE.
- `core/services/ingest_service.py::IngestService(*, observation_repo, watermark_repo, rejected_repo,
  clock)` is DONE.
- `composition/app.py::create_app` shows the canonical Postgres repo wiring to MIRROR (engine via
  `to_psycopg_url(settings.database_url)`; the six `Postgres*Repository(engine)` adapters).

### The flat DQL row-dict shape the Dynatrace executor must produce (per row)
`timestamp` (ISO-8601 str, `Z` ok), `event.id` (str), `synthetic_test.id` (str), `synthetic_test.type`
(str — `"HTTP_CHECK"` routes to `normalize_http_row`), `synthetic_location.name` (str),
`execution.outcome` (str — vendor outcome, mapped by `health_mapping.map_execution_outcome`),
`request.response_time_ms` (optional number). Missing required field ⇒ `MalformedDqlRowError`.

---

## Tasks (TDD; commit after each green; scoped staging — never `git add -A`)

### T1 — Real Dynatrace Grail DQL Executor  *(AC1)*
- **Runtime dep:** move `httpx` from the `dev` extra into `[project] dependencies` in `pyproject.toml`
  (the executors import it at runtime). Command-sync: note it in CLAUDE.md's tooling table.
- **New module** `backend/src/adapters/inbound/dynatrace/grail_executor.py`:
  - `make_grail_executor(*, env_url: str, api_token: str, http_post=httpx.post) -> Executor` — returns a
    closure `Executor` (`Callable[[str], list[dict]]`). The `http_post` seam (default `httpx.post`)
    keeps it unit-testable without a live call.
  - The closure POSTs to `f"{env_url.rstrip('/')}/platform/storage/query/v1/query:execute"` with headers
    `{"Authorization": f"Api-Token {api_token}", "Content-Type": "application/json"}` and JSON body
    `{"query": <the DQL string>}`. Raise a named `GrailQueryError(RuntimeError)` on a non-2xx response
    (include status + a short body excerpt).
  - Map the Grail response to `list[dict]`: Grail returns `{"records": [ {...}, ... ]}` (each record's
    keys are the DQL output columns). Return `response.json()["records"]` (default to `[]` if the key is
    absent). The record keys are expected to already be the flat dotted names above; **if the live tenant
    differs, the mapping is the one place to adjust** (flag in the live smoke — T5).
- **Tests** `backend/tests/test_grail_executor.py` (recorded fixture; NO live call):
  - Fake `http_post` capturing `(url, headers, json)` and returning a recorded Grail JSON
    (`backend/tests/fixtures/dynatrace/grail_http_response.json` — author it from the documented shape,
    one `HTTP_CHECK` record). Assert: endpoint, `Authorization: Api-Token …`, body `{"query": ...}`
    carries the built DQL; and that piping `records` through `normalize_rows(records, signal_key=...)`
    yields a `SignalObservation` (ties the executor output to the existing normalizer contract).
  - Non-2xx (e.g. 401) ⇒ `GrailQueryError`. Empty/absent `records` ⇒ `[]` (empty-input agreement).
- **Module + function docstrings** citing dossier §8.

### T2 — Real Statuspage HTTP Executor  *(AC2)*
- **New module** `backend/src/adapters/outbound/statuspage/http_executor.py`:
  - `make_statuspage_executor(*, http_request=httpx.request) -> Executor` — returns a closure matching
    `Executor = Callable[[method, url, headers, json], dict]` that calls
    `http_request(method, url, headers=headers, json=json)`, raises a named
    `StatuspageApiError(RuntimeError)` on non-2xx (so `BestEffortPublisher` swallows it on the
    recovery-publish path), and returns `response.json()` (or `{}` on empty body).
- **Tests** `backend/tests/test_statuspage_http_executor.py` (recorded fixture; NO live call):
  - Fake `http_request` capturing the call + returning a recorded component JSON. Assert method/url/
    headers/json forwarded verbatim and parsed dict returned; non-2xx ⇒ `StatuspageApiError`.
- **Docstrings** citing dossier §6/§12.

### T3 — Settings + config Statuspage mapping  *(AC3)*
- **`composition/settings.py`** — extend `Settings` (frozen dataclass) with `dynatrace_env_url: str`,
  `dynatrace_api_token: str`, `statuspage_page_id: str`, `statuspage_api_token: str`. `load_settings()`
  reads `DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`, `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`
  (note the env name is `STATUSPAGE_API_KEY`, the field is `statuspage_api_token`). These are REQUIRED
  for the live loop but the API (`create_app`) must still boot without them — so read them with
  `os.environ.get(...)` into `str | None`, OR add a separate `load_runtime_secrets()` used only by the
  live driver. **Chosen:** keep `load_settings()` DB-only as today; add
  `load_live_secrets() -> LiveSecrets` (new frozen dataclass) that reads the four vars and raises a clear
  error naming any missing one. This keeps the API boot path unchanged (no new required env for the
  six-tab API) and isolates the live-loop secrets. Tests: all four present → populated; any missing →
  named error.
- **`composition/config.py`** — add `statuspage_component_id: str | None = None` to `ComponentConfig`.
  Add `Config.statuspage_mapping() -> dict[str, str]` returning `{c.id: c.statuspage_component_id}` for
  every component across apps that HAS one (skip `None`). Tests in `test_config.py`: a component with the
  id is included; one without is skipped; the real `httpcheck.yaml` yields `{"http-check":
  "xdnywbx77npw"}`. (The field is read-only config — NO migration; `seed_topology` does not persist it.)

### T4 — Thread orchestration through `run_periodic`  *(AC4, part 1)*
- **`composition/pull_loop.py`** — `run_periodic` currently calls `run_cycle` WITHOUT the orchestration
  extras (ingest-only). Add the same six optional params (`config`, `observation_repo`,
  `maintenance_repo`, `component_repo`, `decide_service`, `clock`) to `run_periodic` and pass them through
  to `run_cycle`. Keep the existing all-or-none guard semantics (supply all six to orchestrate). `on_cycle`
  must still receive the cycle result; when orchestrating, `run_cycle` returns
  `(IngestResult, DecideAction)` — `on_cycle`'s type widens to `Callable[[IngestResult |
  tuple[IngestResult, DecideAction]], Awaitable[None]]`.
- **Tests** `test_pull_loop.py`: a `run_periodic` test with all six extras (fakes) + a `stop_event`
  asserts `orchestrate_signal` ran (the fake `decide_service` recorded a call) and that `on_cycle`
  received the tuple. Backward-compat: the existing ingest-only `run_periodic` tests stay green.

### T5 — Live composition driver + entrypoint  *(AC4 part 2, AC5 runbook)*
- **New module** `composition/run.py`:
  - `build_live_loop(*, settings, secrets, config, engine, clock) -> list[Coroutine]` (or a small
    `LiveLoop` object) that:
    1. mirrors `create_app`'s repo wiring on one `engine`: `PostgresObservationRepository`,
       `PostgresWatermarkRepository`, `PostgresRejectedObservationRepository`,
       `PostgresMaintenanceRepository`, `PostgresComponentRepository`, `PostgresProposalRepository`,
       `PostgresPublicationRepository`;
    2. `ingest_port = IngestService(observation_repo, watermark_repo, rejected_repo, clock)`;
    3. `dynatrace_executor = make_grail_executor(env_url=secrets.dynatrace_env_url,
       api_token=secrets.dynatrace_api_token)`;
    4. `statuspage_publisher = StatuspagePublisher(page_id=secrets.statuspage_page_id,
       api_token=secrets.statuspage_api_token, component_mapping=config.statuspage_mapping(),
       executor=make_statuspage_executor())`;
    5. `publisher = BestEffortPublisher(RecordingPublisher(statuspage_publisher, publication_repo,
       clock))`;
    6. `decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)`;
    7. one `run_periodic(...)` per `signal` in `config` (signal_key, native_id, watermark_repo,
       ingest_port, executor=dynatrace_executor, interval_seconds=signal.interval_seconds, + the six
       orchestration extras).
  - `seed_topology(config, engine)` once before the loops (orchestrate NOOPs on an unseeded component).
  - `async def main()` / `python -m src.composition.run` entrypoint: `load_settings()` +
    `load_live_secrets()` + `load_config(...)`, build the engine via `to_psycopg_url`, `asyncio.gather`
    the loops; dispose the engine in a `finally`.
- **Tests** `test_run_live_loop.py` (fakes; NO live call, NO DB): assert the assembled publisher is
  `BestEffortPublisher` wrapping `RecordingPublisher` wrapping `StatuspagePublisher`; assert one loop per
  configured signal; assert the orchestration extras are present on each `run_periodic` call (inject a
  fake `run_periodic` capturing kwargs). The resource-lifecycle agreement applies — engine disposed on
  every exit path; a test proves dispose-on-failure.
- **CLAUDE.md** — add the run command (`python -m src.composition.run`, reads `.env`) to Key commands +
  the env-var table; note `httpx` is now a runtime dep (command-sync agreement).
- **Runbook (AC5, manual — append to this plan's "Live smoke" section below).**

---

## Live smoke (T5 runbook — manual, post-merge, NOT a DoD gate)
1. `.env` holds `DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`, `STATUSPAGE_API_KEY`, `STATUSPAGE_PAGE_ID`
   (already filled by the PO). Add a `DATABASE_URL`/`DATABASE_URL_DIRECT` for a DB —
   `python scripts/dev_db.py up --env-file .env.db` starts a throwaway Postgres + migrates; export both.
2. `alembic upgrade head` (already current on a fresh throwaway DB).
3. Run the API (`uvicorn` over `create_app`) AND the live loop (`python -m src.composition.run`) against
   the same DB.
4. In Dynatrace, force the `HTTP_CHECK-DB5792CB88D14CF4` monitor to fail (point it at a bad URL / stop the
   target) for ≥ `major` cycles (5 × 120 s ≈ 10 min).
5. Observe: a degradation proposal appears at `GET /api/v1/approvals`. Approve it
   (`POST /api/v1/approvals/{id}` per the approvals contract). The `xdnywbx77npw` Statuspage component
   flips to the mapped status; a row lands in `publications` (`GET /api/v1/publications`).
6. Record the observation (and any Grail field-name / auth-header adjustment needed) in the retro.

---

## Conventions checklist (held at quality review — standing, 2026-06-27 + amendments)
- **Docstrings** on every new module + public class/function, citing the relevant dossier § — mirror
  peers (`adapter.py`, `publish_helper.py`, `settings.py`, `pipeline.py`).
- **Frozen value/result types enforce cross-field invariants** with `model_validator(mode="after")` +
  test. (T3's `LiveSecrets`/`Settings` are simple field bags — no cross-field invariant — N/A, but the
  "all-fields-present or named error" behavior IS tested.)
- **Empty-input AND non-aligned boundary tests** where a function takes a collection — T1 (empty
  `records` → `[]`), T3 mapping (no components with an id → `{}`).
- **Named domain errors, not leaked stdlib / bare `ValueError`** — `GrailQueryError`, `StatuspageApiError`,
  missing-secret error. Both seams raise on non-2xx so `BestEffortPublisher` can swallow.
- **Fake/adapter parity** — N/A (these are the real adapters behind existing seams; their unit tests use a
  fake transport, not a fake port).
- **TOCTOU mapped-domain-error** — N/A this sprint (no new check-then-act DB write; the approve path is
  unchanged from STORY-014).
- **tz-naive 422 at the edge** — N/A (no new API datetime input).
- **Five-file API shape test** — N/A (no new `api/v1/<feature>/`; the live loop is composition, not API).
- **Scoped staging** (never `git add -A`); **clean committed tree** — the committed HEAD must BE the
  gate-green state (run `ruff format` and COMMIT the reflow; 2026-06-29 agreement).
- **Command-sync** — `httpx` runtime dep + the new run command land with the CLAUDE.md update in the same
  commit.
- **Wiki blast-radius** — at DoD, run the MECHANICAL staleness sweep over ALL `docs/scrum/wiki/*.md`
  (`git diff <verified_sha>..HEAD -- <code_refs>`); `pyproject.toml`, `CLAUDE.md`, `settings.py`,
  `config.py`, `pull_loop.py` touch several articles (`statuspage-publish`, `config-layer`,
  `dev-setup-and-dod`, `architecture-boundary`, `core-pipeline-and-availability`). Update/re-verify every
  one the sweep reports.

## DoD gate (all six exit 0, on a CLEAN committed tree)
`pytest` · `lint-imports` (5 contracts, count unchanged — no new zone/feature) ·
`python scripts/check_fk_direction.py` · `alembic upgrade head` (no new migration this sprint) ·
`ruff check` · `ruff format --check`. Boundary note: the two executors live in `adapters/` and may import
`httpx` (already allowed in `core-independence`'s forbidden list as an *external* package the core can't
touch; adapters importing httpx is fine). `composition/run.py` imports both sides — allowed (composition
is the only both-sides zone).

## Guardrails for the implementer
Build to THIS plan + the STORY-016 AC + the dossier — never to chat history. Do NOT write `.scrum/` board
state. Do NOT run the reviewers / merge. Stop-and-report on genuine ambiguity (especially the Grail
response field names — build to the documented shape and flag it, do NOT invent live behavior) or a 3×
effort overrun.
