# Sprint 48 — Plan (external mode)

**Goal:** Complete the DynamoDB adapter set — publications, maintenance windows,
rejected observations, plus a DynamoDB topology seed — proven for behavioral parity
against the landed DynamoDB-Local harness (STORY-086); and land the three deferred
sprint-47 review minors (STORY-091). Neither story is wired into composition — that is
the cutover (STORY-087), out of scope here.

**Mode:** `external`. The PO drives an external AI agent that builds from this `plan.md`
alone. Per the sprint-47 external-delivery contract (execution-modes.md §2, PO-approved
2026-07-15):

1. **Delivery contract:** the external agent works ONLY on branch `sprint-48`, never
   merges to main. On return the orchestrator reads each diff and **commits per story**
   as the reviewable object before reviewing (a self-reported "done" is a to-verify
   list, never evidence).
2. **Never trust a self-reported gate.** The orchestrator runs its own nine-command
   `yt_gate.py` on the final HEAD; that run is the record of record.
3. **Verification floor (external):** yt-spec-reviewer + yt-quality-reviewer per story
   *regardless of points*, plus the reality gate, before any story goes `board: done`.

**This plan.md is the full contract.** The external implementer infers nothing. Every
method's signature, key schema, edge behavior, and docstring deliverable is stated below,
cited to the producing Postgres code and the established DynamoDB adapter conventions.

---

## Execution order & reasoning

1. **STORY-086** (5 pts) — the epic's next ready slice; unblocks the cutover (STORY-087,
   which depends on 083–086 all accepted). High blast radius (new persistence adapters +
   a second seed path), so it goes first: a blocker here still leaves time to finish 091.
2. **STORY-091** (2 pts) — the three sprint-47 review minors. Ordered second because two
   of its three fixes live in `dynamo_proposal_repository.py`, which 086 does **not**
   touch — so there is no file contention, and 091 is pure low-risk hygiene that benefits
   from the DynamoDB context being fresh (reverse-blast-radius momentum). Drops first if
   delivery runs long.

7 points total — under half of sprint-47's 15, a deliberately calmer commit after a
stretch sprint. Recent velocity: 45→6, 46→8, 47→15.

## Plan-verifier

Dispatched (this is a contract-sensitive **external**-mode sprint — plan.md is the full
contract — and STORY-086 is an adapter/vendor-path story consuming producer contracts).
Verifier result is recorded at the bottom of this file; all GAPS fixed before PO sees the
plan.

## Preconditions (verified at planning, external-mode floor)

- **Baseline green on main.** The sprint-47 final HEAD `143f15a` — where all nine DoD
  commands passed (recorded in the sprint-47 board `final_gate`) — is an ancestor of the
  current main HEAD `a8606e9` (`git merge-base --is-ancestor 143f15a HEAD` → true). No
  backend/frontend/config code is modified in the working tree (`git status --short --
  backend frontend config` is empty). The starting baseline is green.
- **Clean tree at fork.** The only tracked changes present are this sprint's own planning
  artifacts (the `.scrum/backlog.yaml` STORY-091 refinement + the `STORY-091` story file +
  the `docs/scrum/sprints/2026-07-15-sprint-48/` dir), which are committed as the sprint-48
  lock records on branch `sprint-48`. The branch forks from main (`a8606e9`) via
  `git checkout main && git checkout -b sprint-48 && git tag sprint-48-start`.
- **Excluded from the branch:** the untracked stray `report-2026-07-15-051821.html` at the
  repo root is NOT part of this sprint and MUST NOT be committed to `sprint-48` (it is not a
  sprint artifact; leave it untracked or the PO removes it).
- **External agent starting state:** branch `sprint-48` at the lock commit, tree otherwise
  clean. The agent builds the files named below; it infers nothing about starting state.

## DoD in force

The **full nine-command gate is unchanged** this sprint. The AWS-epic DoD amendment
(retire `alembic upgrade head` + `check_fk_direction.py`; adopt DynamoDB-Local pytest +
cfn-lint) is **PENDING until STORY-087/088** per `.scrum/definition-of-done.md` — this
sprint touches neither the Postgres schema nor CloudFormation, so all nine commands remain
in force. `check_fk_direction.py` + `alembic upgrade head` are `requires-env` gated
(DATABASE_URL / DATABASE_URL_DIRECT) — provision a throwaway Postgres via
`scripts/dev_db.py up` for the final gate. The DynamoDB-Local-backed tests need Docker (or
`DYNAMO_ENDPOINT_URL`) for the `dynamo_resource` fixture; without it those tests skip
cleanly, so the reality gate (live parity probe) is mandatory this sprint, not optional.

---

# Established DynamoDB conventions (READ FIRST — the contract every adapter obeys)

These are drawn from the landed adapters (sprints 46–47). The new adapters MUST follow
them exactly; a reviewer rejects any divergence.

- **Table:** one control table, `settings.dynamo_control_table` (default
  `"uptime-control"`). Constructor shape is identical across every adapter:
  ```python
  def __init__(self, db_resource, table_name: str) -> None:
      self._db = db_resource
      self._table_name = table_name
      self._table = self._db.Table(table_name)
  ```
  The new adapters need `self._table_name` (for `transact_write_items` /
  `meta.client`), so follow the adapters that store it —
  `dynamo_proposal_repository.py:23-26` and `dynamo_observation_repository.py:19-22`.
  (Note: `dynamo_component_repository.py:16-18` stores only `_db` + `_table`, no
  `_table_name` — that read-only adapter never needs the low-level client; do NOT
  copy its two-attribute shape.)
- **Datetimes:** serialize/deserialize tz-aware UTC via
  `from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso`
  — NEVER `.isoformat()` inline. Canonical form is `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`
  (`dynamo_serde.py:8-28`). ISO strings sort lexicographically = chronologically, which is
  what makes time-ordered SK ranges work.
- **Counter IDs:** integer surrogate ids come from a per-entity counter partition, via the
  established `_next_id` pattern (`dynamo_proposal_repository.py:48-56`):
  ```python
  def _next_id(self) -> int:
      response = self._table.update_item(
          Key={"pk": "COUNTER", "sk": "<entity>"},   # sk names the sequence
          UpdateExpression="ADD seq :inc",
          ExpressionAttributeValues={":inc": 1},
          ReturnValues="UPDATED_NEW",
      )
      return int(response["Attributes"]["seq"])
  ```
  Each entity uses a DISTINCT `sk`: proposals already use `sk="proposal"`. This sprint adds
  `sk="publication"` and `sk="maintenance"`. **Do not share a counter across entities.**
- **Transactions** use the low-level client, not the resource:
  `client = self._db.meta.client; client.transact_write_items(TransactItems=[...])`
  (`dynamo_proposal_repository.py:109-129`).
- **Numeric reads:** DynamoDB returns numbers as `Decimal`. `int(item["x"])` accepts a
  `Decimal` directly — do NOT branch on `isinstance(..., Decimal)` (STORY-084 quality
  review collapsed exactly that redundancy; `dynamo_observation_repository.py:127-135`).
- **Optional attributes:** never write `None` into an item — omit the key instead, then
  read back with `item.get("x")`. (See the `if ... is not None: item["x"] = ...` pattern
  throughout `dynamo_proposal_repository.py:80-85`.)
- **Topology partition:** components live at `pk="TOPOLOGY"`, `sk="COMPONENT#<id>"`;
  signals at `pk="TOPOLOGY"`, `sk="SIGNAL#<signal_key>"`; apps (added by this sprint's
  seed) at `pk="TOPOLOGY"`, `sk="APP#<id>"` (`dynamo_component_repository.py:30-41`,
  `dynamo_signal_repository.py:30-33`).
- **GSI:** the table has a secondary index named `gsi1` with keys `gsi1pk` / `gsi1sk`
  (used sparsely — an item participates only if it carries both attributes;
  `dynamo_proposal_repository.py:88-90,167-170`). This sprint reuses `gsi1` for the
  maintenance-window ordered listing (see STORY-086 §2).
- **Tests:** the session fixture is `dynamo_resource` (auto-cleaned between tests by
  `clean_dynamo_tables`); get the table name from `load_settings().dynamo_control_table`.
  Pattern: `backend/tests/test_dynamo_proposal_repository.py:20-24`. New tests go in a new
  file per adapter, mirroring the existing `test_dynamo_*_repository.py` naming.

---

# STORY-086 — DynamoDB adapters: publications, maintenance, rejected + seed (5 pts)

Story file: `docs/scrum/stories/STORY-086-dynamodb-publication-maintenance-seed.md`
(AC verbatim there — the AC is the acceptance object, this plan is the build contract).

**New files (all under `backend/src/adapters/persistence/`):**
- `dynamo_publication_repository.py` — `class DynamoPublicationRepository(PublicationRepository)`
- `dynamo_maintenance_repository.py` — `class DynamoMaintenanceRepository(MaintenanceRepository)`
- `dynamo_rejected_observation_repository.py` — `class DynamoRejectedObservationRepository(RejectedObservationRepository)`
- **Seed:** add a DynamoDB seed function. Do NOT modify the existing
  `backend/src/composition/seed.py::seed_topology(config, engine)` or its call sites
  (`app.py:29`, `run.py:187`) — that Postgres path stays live until the cutover
  (STORY-087). Put the new function in a new module
  `backend/src/composition/seed_dynamo.py`:
  `def seed_topology_dynamo(config: Config, db_resource, table_name: str) -> None`.
  (Composition-layer function, same zone as the existing seed; not wired in yet — AC6.)

**New test files (under `backend/tests/`):** one per adapter, plus seed —
`test_dynamo_publication_repository.py`, `test_dynamo_maintenance_repository.py`,
`test_dynamo_rejected_observation_repository.py`, `test_dynamo_seed.py`. All use the
`dynamo_resource` fixture.

## §1 — DynamoPublicationRepository (AC1)

Port: `PublicationRepository` (`backend/src/core/ports/publication_repository.py:22-46`):
```python
def record(self, publication: Publication) -> Publication: ...
def list_recent(self, limit: int = 50) -> list[Publication]: ...
```
Postgres parity source: `publication_repository.py:45-129`. Domain type:
`backend/src/core/domain/publication.py` — `Publication` fields: `component_id: str`,
`status: ComponentStatus`, `published_at: datetime` (tz-aware UTC), `proposal_id: int|None`,
`outcome: PublicationOutcome` (`"succeeded"`/`"failed"`), `id: int|None`,
`author: str|None` (derived on read, NOT persisted by `record`).

### `record(publication) -> Publication`
- Assign an int id via `_next_id()` with counter `sk="publication"`.
- Persist ONE item, a single time-ordered partition so `list_recent` is one descending
  Query:
  - `pk = "PUBLICATION"`
  - `sk = f"{to_canonical_iso(publication.published_at)}#{assigned_id}"` (the `#<id>`
    suffix disambiguates two attempts recorded at the same instant, and keeps SK unique)
  - attributes: `id` (int), `component_id`, `status` = `publication.status.value`,
    `published_at` = the canonical iso string, `outcome` = `publication.outcome.value`.
  - `proposal_id`: write ONLY if not None (omit-when-None convention). This is how
    `list_recent` distinguishes proposal-less publications (author → None).
  - Do NOT persist `author` (parity: Postgres derives it on read; `publication.py:71-72`).
- Return `publication.model_copy(update={"id": assigned_id})` (`Publication` is frozen —
  use `model_copy`, mirroring `dynamo_proposal_repository.py:130`).
- No condition expression needed (every attempt is its own row; a fresh `_next_id` makes
  the SK unique).

### `list_recent(limit=50) -> list[Publication]`
- Query the `PUBLICATION` partition **descending**, capped at `limit`:
  ```python
  resp = self._table.query(
      KeyConditionExpression=Key("pk").eq("PUBLICATION"),
      ScanIndexForward=False,
      Limit=limit,
  )
  ```
  `ScanIndexForward=False` gives newest-first (parity with `ORDER BY published_at DESC`,
  `publication_repository.py:111`). **Do not** post-sort in Python — the SK ordering is
  the contract. A single Query page is correct here because `Limit` caps the result;
  pagination is not required for `list_recent` (unlike `in_window`).
- **Author derivation (the correlated-subquery parity — AC1's crux).** Postgres derives
  `author` from the first approved `approval_events.actor` for the row's `proposal_id`
  (`publication_repository.py:86-113`). STORY-085 denormalized this onto the proposal META
  as the `approved_actor` attribute (set when an `"approved"` event is recorded —
  `dynamo_proposal_repository.py:279-290`). So:
  - Collect the DISTINCT `proposal_id`s present across the queried publications (ints).
  - For those, `BatchGetItem` the proposal META items (`pk=f"PROPOSAL#{pid}"`, `sk="META"`)
    and read `approved_actor` (may be absent → author None). Use
    `self._db.meta.client.batch_get_item` OR `dynamodb.batch_get_item` via the resource;
    handle the 100-key batch limit and `UnprocessedKeys` (chunk if needed — for `limit<=50`
    one batch suffices, but code the loop so a larger limit is safe).
  - A publication with no `proposal_id` → `author=None`. A publication whose proposal has
    no `approved_actor` (e.g. auto-published, or proposal META missing) → `author=None`.
  - Build each `Publication(..., author=<actor or None>)`.
  - **Edge:** empty partition → `list_recent` returns `[]` (no BatchGetItem call on an
    empty key set — `batch_get_item` with zero keys is an error; guard it).

### Tests (AC1)
- `record` assigns increasing int ids; persists both a SUCCEEDED and a FAILED outcome and
  both come back from `list_recent`.
- `list_recent(limit)` returns newest-first and respects the cap.
- Author parity: seed a proposal, record an `"approved"` approval event (actor="alice"),
  record a publication with that `proposal_id` → `list_recent` returns `author="alice"`;
  a publication with `proposal_id=None` → `author=None`; a publication whose proposal was
  never approved → `author=None`.
- **Parity fixture (produce `approved_actor` from real code, never hand-written):** the
  test MUST drive `DynamoProposalRepository.record_approval_event(proposal_id,
  action="approved", actor="alice", occurred_at=...)` — OR a real `ApprovalService.approve`
  — so the `approved_actor` attribute lands on the proposal META exactly as production
  writes it. Do NOT hand-insert an `approved_actor` attribute into the item. The pattern is
  demonstrated at `backend/tests/test_dynamo_proposal_repository.py:197` (an approved-action
  event write). The action value is literally `"approved"` (not `"approve"` — that was the
  STORY-071 CheckViolation trap; the current constant is `"approved"`,
  `dynamo_proposal_repository.py:279`).

## §2 — DynamoMaintenanceRepository (AC2)

Port: `MaintenanceRepository` (`backend/src/core/ports/maintenance_repository.py:13-59`):
```python
def list_windows(self) -> list[MaintenanceWindow]: ...
def create(self, window: MaintenanceWindow) -> MaintenanceWindow: ...
def is_under_maintenance(self, component_id: str, at: datetime) -> bool: ...
def delete(self, window_id: int) -> None: ...
```
Postgres parity source: `maintenance_repository.py:33-119`. Domain type
`MaintenanceWindow` (`maintenance.py:8-52`): `component_id`, `starts_at` (tz UTC),
`ends_at` (tz UTC, strictly > starts_at, enforced in the model), `reason: str|None`,
`title: str|None`, `id: int|None`. `MaintenanceWindowNotFoundError(ValueError)` at
`maintenance.py:55-56`.

### `create(window) -> MaintenanceWindow`
- Assign an int id via `_next_id()` with counter `sk="maintenance"`.
- Persist ONE item:
  - `pk = f"MAINTWIN#{assigned_id}"`, `sk = "META"`
  - attributes: `id`, `component_id`, `starts_at` = `to_canonical_iso(window.starts_at)`,
    `ends_at` = `to_canonical_iso(window.ends_at)`; `reason`/`title` omitted-when-None.
  - **GSI for ordered listing:** `gsi1pk = "MAINT"`,
    `gsi1sk = f"{to_canonical_iso(window.starts_at)}#{assigned_id}"`. (Reuses the existing
    `gsi1` index; `#<id>` suffix keeps gsi1sk unique across two windows starting at the
    same instant.)
- Return `window.model_copy(update={"id": assigned_id})` (frozen model).

### `list_windows() -> list[MaintenanceWindow]`
- Query `gsi1` on `gsi1pk = "MAINT"`, ascending (default `ScanIndexForward=True`), so the
  natural gsi1sk order = starts_at ascending (parity: `ORDER BY starts_at`,
  `maintenance_repository.py:42`). Map each item back to `MaintenanceWindow`.
- Empty → `[]`.

### `is_under_maintenance(component_id, at) -> bool`
- Boundary semantics MUST be **inclusive start, exclusive end**: return True iff there
  exists a window for `component_id` with `starts_at <= at < ends_at`. Postgres form is
  `starts_at <= :at AND ends_at > :at` (`maintenance_repository.py:97-101`).
- **PO-accepted eventual-consistency delta (2026-07-14):** the `gsi1` read may miss a
  window created seconds earlier (GSIs are eventually consistent, and GSI reads cannot be
  made consistent). This is accepted — windows are scheduled ahead of time. Document it
  (AC5).
- Implementation: Query `gsi1` on `gsi1pk="MAINT"` with `KeyConditionExpression` bounding
  `gsi1sk <= f"{to_canonical_iso(at)}#￿"` (all windows started at or before `at`;
  the `￿` high-sentinel makes the `#<id>` suffix inclusive), then in a
  `FilterExpression` require `ends_at > :at AND component_id = :cid`. Return whether any
  item matches. (The GSI narrows to started windows; the filter applies the exclusive-end
  and component predicates. Do not scan the whole partition in Python.)
  - **Alternative acceptable if simpler & proven:** Query `gsi1pk="MAINT"` +
    `FilterExpression` on all three predicates (`starts_at <= :at AND ends_at > :at AND
    component_id = :cid`). Either is fine provided both boundary instants are tested.
- **Edge tests (AC2, both instants):** a window `[T0, T1)` →
  `is_under_maintenance(c, T0) is True` (inclusive start),
  `is_under_maintenance(c, T1) is False` (exclusive end),
  `is_under_maintenance(c, midpoint) is True`, and a different component → False.

### `delete(window_id) -> None`
- Delete `pk=f"MAINTWIN#{window_id}"`, `sk="META"` with
  `ConditionExpression="attribute_exists(pk)"`. On `ConditionalCheckFailedException`
  raise `MaintenanceWindowNotFoundError(f"Maintenance window with ID {window_id} not
  found.")` (message parity: `maintenance_repository.py:117-119`). Wrap the low-level
  `ClientError` like `dynamo_component_repository.py:61-64`.
- Test: delete an existing window (gone from `list_windows`); delete a missing id raises
  `MaintenanceWindowNotFoundError`.

## §3 — DynamoRejectedObservationRepository (AC3)

Port: `RejectedObservationRepository`
(`backend/src/core/ports/rejected_observation_repository.py:18-34`):
```python
def save(self, *, signal_key: str | None, reason: str, payload: dict,
         rejected_at: datetime) -> None: ...
```
Postgres parity source: `rejected_observation_repository.py:38-58`. **No domain type** —
raw params (the scout confirmed no `RejectedObservation` domain class exists; do not
invent one). Append-only quarantine; no port reads it back.

### `save(*, signal_key, reason, payload, rejected_at) -> None`
- Persist ONE item; a fresh uuid keeps the SK unique (append-only, every rejection is its
  own row — parity note `rejected_observation_repository.py:46-49`):
  - `pk = f"REJECTED#{signal_key if signal_key is not None else 'UNKNOWN'}"`
  - `sk = f"{to_canonical_iso(rejected_at)}#{uuid4()}"` (import `from uuid import uuid4`;
    `str(uuid4())`)
  - attributes: `reason` (str), `payload` (the dict, stored as a Map),
    `rejected_at` = canonical iso; and store `signal_key` as an attribute too (may be
    None → omit per convention, but the pk already encodes UNKNOWN).
- **Never fails on unknown/absent signal_key** (AC3) — the `UNKNOWN` pk partition absorbs
  it; there is no condition expression and no FK. This mirrors the Postgres table's
  deliberate no-FK-on-signal_key design (`rejected_observation_repository.py:7-11`).
- **payload caveat:** DynamoDB Maps reject empty strings? No — empty strings are allowed
  since 2020. But floats must be `Decimal` if present. Payloads here are raw DQL/vendor
  dicts; if a payload can contain a float, convert via
  `json.loads(json.dumps(payload), parse_float=Decimal)` before Put (the boto3 resource
  serializer rejects native `float`). State this in the docstring; test with a payload
  containing a nested dict and a numeric value.

### Tests (AC3)
- `save` with a normal `signal_key` persists reason + full payload map (read the raw item
  back via `get_item` and assert `reason` and `payload` round-trip).
- `save(signal_key=None, ...)` succeeds (lands under `REJECTED#UNKNOWN`), does not raise.
- Two saves for the same signal_key at the same instant both persist (distinct uuids).

## §4 — seed_topology_dynamo (AC4)

New function `backend/src/composition/seed_dynamo.py::seed_topology_dynamo(config: Config,
db_resource, table_name: str) -> None`. Parity source: `seed.py:48-118`. Reads
`config.apps` (list of `AppConfig`), each with `.components` and `.signals`
(`AppConfig`/`ComponentConfig`/`SignalConfig` in `composition/config.py`).

- **Idempotent PutItems** (no transaction — the seed re-runs at every boot of both
  processes; double-seeding stays safe; atomicity dropped deliberately per STORY-017 D3,
  quoted in the story Context). Upsert order is irrelevant for DynamoDB (no FKs) but keep
  apps → components → signals for readability.
- **Apps:** `pk="TOPOLOGY"`, `sk=f"APP#{app.id}"`; attributes `id`, `name`,
  `config={"thresholds": app.thresholds.model_dump()}` (parity: `seed.py:63-66`).
- **Components:** `pk="TOPOLOGY"`, `sk=f"COMPONENT#{comp.id}"`; attributes `id`, `app_id`,
  `name`, **and `status`** — BUT status must be seeded **only if the component item does
  not already exist**, and NEVER overwritten on re-seed (parity: the Postgres upsert's
  `set_` updates name+app_id but not status — `seed.py:86-93`; and
  `DynamoComponentRepository._map_item` requires a `status` attribute —
  `dynamo_component_repository.py:20-26`). Implementation:
  - Two-step per component: `update_item` on `pk="TOPOLOGY"`,`sk=f"COMPONENT#{comp.id}"`
    with `UpdateExpression="SET #n=:name, app_id=:aid, #s=if_not_exists(#s, :default)"`,
    names `{"#n":"name","#s":"status"}`, values
    `{":name":comp.name, ":aid":app.id, ":default": ComponentStatus.OPERATIONAL.value}`.
    `if_not_exists` sets `status` to the default on first write and leaves an existing
    status untouched on re-seed — exact parity with "name/app_id updated, status
    preserved". **The default value is `"operational"`** — verified: the Postgres
    `components.status` column carries `server_default="operational"`
    (`migrations/versions/3a8254bcfe59_spine_schema.py:123`), which equals
    `ComponentStatus.OPERATIONAL.value` (`core/domain/status.py:23`). The Postgres seed
    never sets status (`seed.py:86-93` updates only name+app_id), so a newly-seeded
    Dynamo component must land in `operational`, matching the DB column default.
- **Signals:** `pk="TOPOLOGY"`, `sk=f"SIGNAL#{sig.signal_key}"`; attributes `signal_key`,
  `app_id`, `name`, `component_id` (omit-when-None), `interval_seconds`
  (`if_not_exists` NOT needed — all signal attributes are config-derived and updated on
  re-seed, parity `seed.py:106-114`). Plain `put_item` (full overwrite) is fine for
  signals since every attribute is config-owned.

### Tests (AC4)
- Seed once → apps/components/signals present with expected attributes (read back via the
  existing `DynamoComponentRepository`/`DynamoSignalRepository` to prove they map cleanly).
- Seed twice → identical state (idempotent).
- Changed config value (e.g. a signal `name`) → reflected on re-seed.
- **Status preservation:** seed; set a component's status to DEGRADED via
  `DynamoComponentRepository.set_status`; re-seed; assert the status is STILL DEGRADED
  (component `status` NOT reset — AC4's explicit clause, the STORY-071-class parity trap).

## §5 — Consistency delta + boundaries (AC5, AC6)

- **AC5:** document the maintenance GSI eventual-consistency delta in
  `DynamoMaintenanceRepository`'s class docstring AND in the wiki persistence-zone article
  (create/update — see Wiki below). One sentence, citing the PO acceptance (2026-07-14).
- **AC6:** import-linter contracts pass (these are pure `adapters/persistence` +
  `composition` additions — no core→adapter edge, no adapter→adapter import; the seed
  imports `Config` from composition, which is legal for the composition zone). Six backend
  gates green. **Not wired into composition** — do NOT touch `app.py`/`run.py`/`settings`
  wiring; the adapters and the dynamo seed are constructed only in tests this sprint.

## Wiki (STORY-086 forward blast radius)

`docs/scrum/wiki/` — the persistence-zone article(s) covering the DynamoDB adapters. Add
the three new adapters + the dynamo seed to `code_refs`; record the maintenance
eventual-consistency delta (AC5). Bump `verified_sha` at DoD. (The orchestrator resolves
the exact article + runs the sweep at the compile pass; the implementer should leave the
adapters documented well enough — clear class docstrings — that the article update is
mechanical.)

---

# STORY-091 — sprint-47 review minors (2 pts)

Story file: `docs/scrum/stories/STORY-091-sprint47-review-minors.md` (AC verbatim there).
Three independent low-risk hygiene fixes. No behavior change except AC1's guard.

## AC1 — proposal-event orphan guard
File: `backend/src/adapters/persistence/dynamo_proposal_repository.py`,
`record_approval_event` (lines 243-296). Today the event `Put` (lines 270-276) has NO
condition; only the optional approved-actor `Update` (action=="approved") carries
`attribute_exists(pk)`. So a **rejection** event (action=="rejected") against a
non-existent proposal would write an orphan event item with no guard.
- **Fix:** add `"ConditionExpression": "attribute_exists(pk)"` to the event `Put` so an
  event against a missing proposal fails and writes nothing — parity with the Postgres FK
  guard. The condition checks the event item's own `pk` (`PROPOSAL#<id>`), which the META
  item shares; note that a transaction with two writes to items sharing a `pk` is fine (an
  event and the META are different `sk`s). Because a `TransactWriteItems` is
  all-or-nothing, a failed condition cancels the whole transaction and writes nothing.
- **Latency note:** this is currently unreachable via `ApprovalService._decide` (which
  loads + resolves the proposal first), so it is latent-divergence hygiene, not a live bug
  — state that in the code comment.
- **Test:** call `record_approval_event(999, action="rejected", ...)` for a proposal id
  that was never created → expect a `ClientError`/`TransactionCanceledException` raised AND
  assert no event item exists (`get_item` on the would-be event key returns nothing). Also
  assert the existing happy path (event against a real proposal) still succeeds.

## AC2 — blocker-fixture return-code check
File: `backend/tests/test_dev_db_cli.py`, autouse `run_with_blocker` fixture (lines 36-64).
Today it starts a "blocker" container to prove `dev_db.py`'s dynamic-name/free-port design
is collision-proof, but ignores the docker return code — so if the blocker never comes up,
the collision-proof claim passes vacuously.
- **Fix (implementer's choice, record it):** EITHER (a) assert the blocker's `docker`
  subprocess returned 0 (blocker actually started) before yielding, keeping the post-yield
  finalizer leak-free; OR (b) if the blocker is judged purely decorative given the
  dynamic-name/port design already guarantees isolation, remove it and rely on that design.
  Record the decision in the fixture docstring + story History.
- **Test:** the existing `test_dev_db_cli.py` tests must still pass (this fixture is
  autouse for that module). If (a): the assertion is the test. No new test file needed.

## AC3 — create_open dedup
File: `dynamo_proposal_repository.py`, `create_open` (lines 70-107). The `meta_item`
(70-90) and `slot_item` (93-107) blocks copy the same base fields (id, component_id,
to_status.value, state.value, proposed_at) and the same three optionals (from_status,
reason, resolved_at). `meta_item` additionally gets the sparse GSI attrs when OPEN.
- **Fix:** factor the shared field-copy through a small local helper (e.g.
  `_base_proposal_attrs(proposal, assigned_id, proposed_at_str, resolved_at_str) -> dict`)
  that returns the common base + optional attrs; each caller adds its own `pk`/`sk` (and
  `meta_item` adds the GSI attrs). **No behavior change** — the resulting items must be
  byte-identical to today.
- **Test:** the existing `test_dynamo_proposal_repository.py` suite (create_open,
  one-open-per-component, counter ids, resolve) must all still pass unchanged — that IS
  the regression proof for a no-behavior-change refactor.

## AC4 — gates
Full DoD gate green; import-linter contracts pass; wiki blast radius resolved (sweep
decides — the 091 changes touch `dynamo_proposal_repository.py`, which may be a `code_ref`;
re-verify or update the article at the compile pass).

---

## Definition-of-Done checklist (both stories, every commit)
- [ ] `pytest` → exit 0 (needs Docker/`DYNAMO_ENDPOINT_URL` for dynamo tests + a throwaway
      Postgres for the DB-gated ones; provision via `scripts/dev_db.py up`)
- [ ] `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` → exit 0
- [ ] `python scripts/check_fk_direction.py` → exit 0 (requires-env: DATABASE_URL)
- [ ] `alembic upgrade head` → exit 0 (requires-env: DATABASE_URL_DIRECT)
- [ ] `ruff check .` → exit 0
- [ ] `ruff format --check .` → exit 0
- [ ] `npm test` / `npm run build` / `npm run lint` (frontend — untouched this sprint, must
      stay green)
- [ ] Every AC has a test exercising it.
- [ ] Reality gate: live parity probe against `dynamo_resource` — the author-derivation
      path (086 §1) and the maintenance boundary instants (086 §2) each executed once
      against a real DynamoDB-Local, not asserted only against hand-built items.

---

## Plan-verifier result

Dispatched at planning (external + adapter/contract-sensitive). **11/11 technical checks
PASS**, verdict GAPS on 3 specification/precondition-hygiene items (no logic errors). All
three fixed before the PO saw this plan:

- **PASS (re-verified against producing code):** port signatures (all three ports exact);
  DynamoDB conventions (COUNTER pk, gsi1/gsi1pk/gsi1sk per `create_tables.py:78-85`, serde,
  transaction client, int(Decimal), omit-None); author-derivation parity chain
  (`action="approved"` → `approved_actor` on PROPOSAL#/META → Postgres subquery filter);
  maintenance boundary (`starts_at<=at AND ends_at>at`, high-sentinel range sound, no
  off-by-one); seed status-preservation (default `"operational"` from the spine migration
  server_default); seed non-modification boundary; 091 orphan-guard soundness + unreachable-
  via-ApprovalService claim; 091 create_open byte-identical refactor; AC↔breakdown trace
  both stories; DoD nine-in-force / amendment-pending-until-087.
- **GAP 1 (precondition) → FIXED:** added the Preconditions section (baseline green,
  `143f15a` ancestor of main, clean tree, fork point, stray report excluded).
- **GAP 2 (citation) → FIXED:** constructor-shape now cites
  `dynamo_proposal_repository.py:23-26` / `dynamo_observation_repository.py:19-22` (the
  adapters that store `_table_name`), with a note that the component repo's 2-attr shape is
  NOT the one to copy.
- **GAP 3 (dangling ref) → FIXED:** replaced "STORY-066 fixture script" with the concrete
  instruction to drive `record_approval_event(action="approved")` / `ApprovalService.approve`
  (pattern at `test_dynamo_proposal_repository.py:197`), plus the `"approved"`-not-`"approve"`
  STORY-071 note.

Status after fixes: **LOCK_READY.**
