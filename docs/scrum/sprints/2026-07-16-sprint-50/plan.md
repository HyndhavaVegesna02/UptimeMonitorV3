# Sprint 50 Plan — Deploy for real: live console deployment + sprint-49 hardening

- **Sprint goal:** Harden the container image and stack (STORY-093), then execute the
  live console deployment and verify the deployed system end-to-end (STORY-089) —
  completing the AWS migration epic's deployment leg.
- **Mode:** `in-process` (STORY-093 via yt-implementer; STORY-089 is PO-driven — console
  actions are sanctioned PO-interaction points per the story's Context, with the
  orchestrator verifying every AC live and recording evidence).
- **Stories & order:**
  1. **STORY-093** (2 pts) — sprint-49 review minors: container hardening, ECS health
     grace, test hygiene. **First** because its Dockerfile hardening and
     `HealthCheckGracePeriodSeconds` must be in the image/template that STORY-089
     actually deploys (dependency ordering, not just size).
  2. **STORY-089** (3 pts) — live console deployment + e2e verification (PO-driven).
- **Plan-verifier:** DISPATCHED — the sprint is contract-sensitive (STORY-089 exercises
  the vendor/deploy path live; STORY-093 AC2 edits the CloudFormation service contract;
  the Dockerfile dep-layer change touches the build contract STORY-089 pushes to ECR).
- **Tooling gaps:** none. AWS console access + live credentials are the PO's side of
  STORY-089 (as approved at refinement 2026-07-14).

---

## STORY-093 — Chore: sprint-49 review minors (2 pts)

### Verified contracts / constraints (cited from producing code)

- `Dockerfile:14` today: `RUN pip install --no-cache-dir . uvicorn[standard]` runs AFTER
  `COPY backend /app/backend` (line 10) — any source edit invalidates the pip layer.
  Constraint: `pip install .` requires `backend/` present (`package-dir = {"" = "backend"}`
  in `pyproject.toml`), so the cached dependency layer must derive deps from
  `pyproject.toml` alone — e.g. a stdlib `tomllib` one-liner emitting the
  `[project] dependencies` list to pip — BEFORE `backend/` is copied; the final
  `pip install .` of the package itself then rides on already-installed deps.
- `Dockerfile:6` `ENV PORT=8000` is dead: `CMD` (line 19) hard-codes `--port 8000`;
  `infra/stack.yaml` task definitions inject no `PORT` var (verified STORY-088 trace).
- Non-root: the app binds 8000 (unprivileged) and only reads `/app`; a passive
  `USER` added after install is safe. The loop role (`CMD` override
  `python -m src.composition.run`) writes nothing to disk either (env + network only).
- `infra/stack.yaml:381` `APIService` has no `HealthCheckGracePeriodSeconds`;
  `HealthCheckGracePeriodSeconds` is a valid `AWS::ECS::Service` property (root of
  `Properties`, integer seconds). Target group probes `/api/v1/health` every 30s,
  unhealthy after 3 fails (`stack.yaml:364-368`) ≈ 90s budget; the boot lifespan seed
  (config read + DynamoDB writes) can exceed that on a cold task. Set **120**.
- `backend/tests/test_run_live_loop.py:248` `test_main_resource_lifecycle_success`
  currently ends at `asyncio.run(main())` with zero assertions (the dispose check was
  removed with the engine). The patched mocks (`mock_seed_topology_dynamo`,
  `mock_build_loop`, `mock_make_dynamo_resource`) are the assertable surface.
- `backend/tests/test_topology_endpoint.py:181-197` uses raw `os.environ` try/finally
  for `CONFIG_DIR`; the test already receives pytest fixtures, so `monkeypatch.setenv`
  is a drop-in.
- Guard-test scope (plan step-4 invariant from sprint-49): no file under `backend/src`
  may contain `sqlalchemy`, `create_engine`, or `psycopg` — scan file contents
  case-sensitively, `.py` files only; the test lives with the other meta-tests
  (alongside the zone-layout meta-test pattern).

### Steps

- [x] 1. Test hygiene first (pure-test commit): add the no-Postgres guard test
  (walk `backend/src/**/*.py`, assert none of `sqlalchemy` / `create_engine` /
  `psycopg` appears); run it — green (invariant holds today). Commit.
- [x] 2. Give `test_main_resource_lifecycle_success` real assertions: after
  `asyncio.run(main())`, assert `mock_make_dynamo_resource` called once,
  `mock_seed_topology_dynamo` called once with exactly
  `(config, db_resource, "uptime-control")` — the real call shape is
  `seed_topology_dynamo(config, db_resource, settings.dynamo_control_table)`
  (`run.py:202`; default table `"uptime-control"`, `settings.py:22`) — and
  `mock_build_loop` called once. See it pass. Commit.
- [x] 3. Replace the raw `os.environ` try/finally in `test_topology_endpoint.py`
  with `monkeypatch.setenv("CONFIG_DIR", ...)`; run the file. Commit.
- [x] 4. Dockerfile hardening: reorder so `COPY pyproject.toml` + dependency
  install (deps derived from `pyproject.toml` via stdlib `tomllib`, plus
  `uvicorn[standard]`) precede `COPY backend/ config/`; final `pip install --no-cache-dir .`
  after source copy; delete `ENV PORT=8000`; add a non-root `USER` (create an
  `app` user) after installs. Commit.
- [x] 5. Reality check the image (adapter-type story ⇒ live probe): `docker build`
  twice with a whitespace-only `backend/` source touch between — assert the dependency
  layer is CACHED on the second build; run the container import smoke
  (`python -c "import src.composition.asgi; import src.composition.run"`) and
  `whoami` inside the container → the non-root user. Record output. Commit any fix.
- [x] 6. `infra/stack.yaml`: add `HealthCheckGracePeriodSeconds: 120` to
  `APIService.Properties`; run `cfn-lint infra/stack.yaml` → exit 0. Commit.
- [x] 7. Runbook branch reconcile: update `docs/deploy-runbook.md` Prerequisite 4
  (currently "Git branch `sprint-49` checked out", line 13) to the `sprint-50`
  branch HEAD — a PO executing the runbook verbatim must deploy the template and
  image that INCLUDE this story's hardening, not sprint-49 artifacts. Commit.
- [x] 8. Story gate: `yt_gate.py --only` scoped to pytest + ruff + cfn-lint (diff
  touches backend tests, Dockerfile, stack.yaml — no frontend). Wiki blast radius:
  `deployment-and-infra.md` / `deployment` articles citing the Dockerfile or
  `stack.yaml` get updated or re-verified. Board → done pending review.
  (Ran the full 8-command DoD gate, incl. import-linter + frontend, per AC4's
  "full amended DoD gate ... + frontend" — all 8 green at a8700f5.)

### Reality gate (093)
Step 5 IS the live probe (docker build + layer-cache assert + in-container smoke +
non-root verify). cfn-lint + the STORY-089 live deploy exercise AC2 for real.

---

## STORY-089 — Live console deployment + e2e verification, PO-driven (3 pts)

The PO executes `docs/deploy-runbook.md` (Steps 1–5) in the AWS console; the
orchestrator drives verification after each step and records evidence in
`sprint-current.yaml`. No code is written unless verification finds a defect
(which then becomes a fix commit on the sprint branch, or a blocker).

### Verified contracts / constraints

- Runbook: `docs/deploy-runbook.md` — Step 1 stack creation, Step 2 Secrets Manager
  values, Step 3 ECR build/tag/push, Step 4 SPA build + S3 upload, Step 5 verification
  checklist. STORY-093 must be merged into the sprint branch BEFORE Step 3's image
  build and Step 1's template upload (order rule above).
- Fresh-start cutover: no data migration; topology seeds from `config/apps` at boot,
  observations regenerate from Dynatrace, watermarks establish on cycle 1.
- Secrets: `DYNATRACE_ENV_URL`/`DYNATRACE_API_TOKEN`/`STATUSPAGE_PAGE_ID`/
  `STATUSPAGE_API_KEY` live ONLY in Secrets Manager (stack references two secret ARNs);
  plain env vars (`AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`)
  are injected by the task definitions (runbook §"Environment variables injected by
  the stack").

### Steps (each ▶ is a sanctioned PO console action; each ✔ is orchestrator verification)

- [ ] 1. Preflight: STORY-093 done on the sprint branch; the PO's checkout for all
  runbook steps is the `sprint-50` HEAD that includes STORY-093 (runbook
  Prerequisite 4 updated by STORY-093 step 7 — never sprint-49); `cfn-lint` green;
  `docker build` green locally; frontend `npm run build` green.
- [ ] 2. ▶ PO runs runbook Step 1 (stack create) + Step 2 (secret values).
  ✔ AC1a: stack `CREATE_COMPLETE`; secrets exist; no secret value pasted anywhere
  in the repo/chat transcript that would be committed (AC5).
- [ ] 3. ▶ PO runs runbook Step 3 (ECR push — image built from the sprint-branch
  HEAD including STORY-093) and forces new deployments if services pre-started.
  ✔ AC1b: both ECS services steady (api task healthy in the target group; loop
  DesiredCount 1 with exactly one RUNNING task).
- [ ] 4. ▶ PO runs runbook Step 4 (SPA build + S3 upload + CloudFront invalidation,
  unconditional per runbook Step 4.4). ✔ AC2: CloudFront URL over HTTPS renders all six tabs; browser
  network panel shows `/api/*` served same-origin (no CORS errors).
- [ ] 5. ✔ AC3 (live loop): watermark item in the control table advances across ≥2
  loop cycles; `/api/v1/availability` (with window) and `/api/v1/history` return
  real observation data for the seeded signal via the CloudFront URL.
- [ ] 6. ▶+✔ AC4 (mutation round-trip): from the deployed UI, toggle sample-mode ON
  → verify the control-table item flipped in DynamoDB (console or CLI) → toggle OFF
  and re-verify (leaves prod clean). Fallback path: maintenance schedule + delete.
- [ ] 7. ✔ AC5 sweep: `git log -p sprint-50 --` scan (and `git grep` at HEAD) for any
  secret value committed during the sprint → none.
- [ ] 8. AC6 docs: append the deployed-topology section to CLAUDE.md (stack name,
  services, env var/secret NAMES, verify commands); create wiki
  `deployment-topology.md` with `code_refs`: `infra/stack.yaml`, `Dockerfile`,
  `docs/deploy-runbook.md` and live-verified facts; record all evidence in
  `sprint-current.yaml`. Commit.
- [ ] 9. Story gate: full amended 8-command gate on final HEAD (this is also the
  sprint-close full gate) + wiki sweep (`yt_wiki.py` exit 0).

### Reality gate (089)
The story IS a reality gate — every AC is a live probe of the deployed stack; evidence
recorded per step in `sprint-current.yaml`. Nothing ships on promise: if a console step
cannot complete (account/credential/limit issues), the story goes Blocked with the exact
failing step, never "done pending deploy".

### Blocked/rollback notes
- Stack create fails → PO deletes the stack (DeletionPolicy Retain protects the two
  tables + ECR repo per STORY-088); fix template on the sprint branch; retry.
- A defect found live = fix commit on sprint-50 (TDD where testable) + re-push image /
  re-upload SPA as needed; if it exceeds the story's effort cap, Blocked + review.
