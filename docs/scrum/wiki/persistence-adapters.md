---
title: Persistence adapters — the repository implementations
code_refs: [backend/tests/test_component_repository_contract.py, backend/tests/test_signal_repository_contract.py, backend/src/core/queries/availability.py, backend/tests/conftest.py, backend/tests/fakes.py, backend/src/adapters/persistence/dynamo_signal_repository.py, backend/src/adapters/persistence/dynamo_component_repository.py, backend/src/adapters/persistence/dynamo_watermark_repository.py, backend/src/adapters/persistence/dynamo_sample_mode_repository.py, backend/src/adapters/persistence/dynamo_serde.py, backend/tests/test_dynamo_adapters.py, backend/src/adapters/persistence/dynamo_publication_repository.py, backend/src/adapters/persistence/dynamo_maintenance_repository.py, backend/src/adapters/persistence/dynamo_rejected_observation_repository.py, backend/src/adapters/persistence/dynamo_proposal_repository.py, backend/src/composition/seed_dynamo.py, backend/src/adapters/persistence/topology_keys.py, backend/tests/test_topology_keys.py, backend/tests/test_dynamo_publication_repository.py, backend/tests/test_dynamo_maintenance_repository.py, backend/tests/test_dynamo_rejected_observation_repository.py, backend/tests/test_dynamo_seed.py, backend/tests/test_dynamo_proposal_repository.py, backend/tests/pagination_diagnostics.py]
tier: map
verified_sprint: sprint-68
status: verified
# Re-verified 2026-07-30 (sprint-65) WITHOUT content change. Touched only via conftest.py.
# NOTE for a future story: RejectedObservationRepository is now written by the PULL LOOP as well as
# by IngestService (STORY-190) -- the port and its Dynamo implementation are unchanged, so no Fact
# here is wrong, but the set of callers has grown.
# tier: map, `verified_sha` dropped 2026-08-12 (yourteam 2.3.0): the staleness baseline is now
# this article's own last commit, derived by git, so there is no stamp to keep current.
# WHAT THIS EDIT DID AND DID NOT VERIFY: it did not re-read these Facts against code. It
# established, per-article, that NO code_ref has moved since this article's last commit
# (`git diff <that commit>..HEAD -- <code_refs>` -> empty, and the sweep is CLEAN at HEAD),
# so the verification earned at sprint 68 is not invalidated by anything since. That is
# the same guarantee `status: verified` has always carried here; the frontmatter migration
# adds no new claim. Articles nobody could make that statement for were demoted to `stale`
# in the same pass, not laundered.
---

## Facts (verified against code)

The concrete DynamoDB implementations of the core's persistence ports (STORY-082, STORY-083, STORY-086, Zone 2). They live in `backend/src/adapters/persistence/`; all DynamoDB interaction code stays here (the `core-independence` contract forbids boto3 or DynamoDB logic in `src.core`). Each imports inward (`src.core.ports`, `src.core.domain`) and never another adapter.

### DynamoDB Repositories

- Implements DynamoDB adapters in `backend/src/adapters/persistence/`:
  - `DynamoSignalRepository` (`dynamo_signal_repository.py`)
  - `DynamoComponentRepository` (`dynamo_component_repository.py`)
  - `DynamoWatermarkRepository` (`dynamo_watermark_repository.py`)
  - `DynamoSampleModeRepository` (`dynamo_sample_mode_repository.py`)
  - `DynamoPublicationRepository` (`dynamo_publication_repository.py`)
  - `DynamoMaintenanceRepository` (`dynamo_maintenance_repository.py`)
  - `DynamoRejectedObservationRepository` (`dynamo_rejected_observation_repository.py`)
  - `DynamoObservationRepository` (`dynamo_observation_repository.py`)
  - `DynamoProposalRepository` (`dynamo_proposal_repository.py`)
- They take `db_resource` (boto3 DynamoDB resource) and `table_name: str` in their constructor, preventing direct dependencies on `src.composition` to adhere to the `adapters-edge-only` boundary contract.
- Point-reads for decision-path queries (`DynamoComponentRepository.get`, `DynamoWatermarkRepository.get`, `DynamoSampleModeRepository.is_enabled`) use `ConsistentRead=True` to guarantee read-after-write consistency.
- `DynamoComponentRepository.set_status` uses conditional updates (`ConditionExpression="attribute_exists(pk)"`) to raise `ComponentNotFoundError` when updating a non-existent component.
- `DynamoPublicationRepository` implements `list_recent` descending Query under the `PUBLICATION` partition, resolving authors via BatchGetItem on distinct proposal METAs using the denormalized `approved_actor` attribute.
- `DynamoMaintenanceRepository` stores windows under `MAINTWIN#<id>`/`META` and indexes them on `gsi1` using `gsi1pk="MAINT"`, `gsi1sk="<starts_at>#<id>"` for starts_at ascending list queries.
  - **GSI eventual consistency:** Since GSI reads are eventually consistent, `is_under_maintenance` query results may miss windows created seconds earlier. This is an accepted design trade-off because maintenance windows are scheduled ahead of time (PO-accepted 2026-07-14).
- **Pagination (STORY-199, ZR-7 fix).** `DynamoComponentRepository.list_components`, `DynamoSignalRepository.list_signals` and `DynamoMaintenanceRepository.list_windows` each loop on `LastEvaluatedKey`/`ExclusiveStartKey` (the `dynamo_observation_repository.py::in_window` pattern) instead of reading a single DynamoDB page, and each carries a test-only `self._limit` hook (mirroring `dynamo_observation_repository.py:23`) so a test can force a small page size without a real 1MB of data — proven by `test_dynamo_component_repository_list_components_paginates`, `test_dynamo_signal_repository_list_signals_paginates` (`backend/tests/test_dynamo_adapters.py`) and `test_dynamo_maintenance_repository_list_windows_paginates` (`backend/tests/test_dynamo_maintenance_repository.py`).
  - `DynamoMaintenanceRepository.is_under_maintenance` also paginates, but as a BOOLEAN short-circuit, not a collect-all loop: it returns `True` on the first page whose post-filter `Items` is non-empty, and returns `False` only once `LastEvaluatedKey` is absent — it must never terminate on an empty-after-filter page, because the GSI `KeyConditionExpression` matches every window ever created and the `component_id`/`ends_at` `FilterExpression` is applied by DynamoDB AFTER the page read, so a component's only matching window can sit several empty-after-filter pages in. Pinned by `test_dynamo_maintenance_repository_is_under_maintenance_paginates_past_forced_page_size` (`backend/tests/test_dynamo_maintenance_repository.py`), which seeds five other-component windows ahead of the one real match with `_limit=1` and asserts `True`.
  - `DynamoProposalRepository.list_open` (`backend/src/adapters/persistence/dynamo_proposal_repository.py`) has the same collect-all loop, proven by `test_dynamo_proposal_repository_list_open_paginates` (`backend/tests/test_dynamo_proposal_repository.py`); both files are also `code_refs` here.
  - The standing guard for all five is ZR-7's pagination test in [[zone-rules]]; `DynamoPublicationRepository.list_recent`'s `Limit=limit` remains the one PERMANENT exemption there because its port promises "up to `limit`", a stated bound, not completeness.
  - **(STORY-213, 2026-08-13) Self-diagnosing assertions, not a fixture change.** `test_dynamo_component_repository_list_components_paginates` failed once in eleven full-suite runs with a bare set-equality mismatch — indistinguishable, by message alone, from a real regression of the loop above. All five `_limit`-forcing tests now wrap the repository's table in `PaginationSpy` (`backend/tests/pagination_diagnostics.py`) so a failure additionally reports the observed page count and whether `LastEvaluatedKey` was present when the loop exited. Mutation-confirmed the two shapes are opposite signatures: forcing DynamoDB Local to hand an absent `LastEvaluatedKey` to an unmodified, correct loop reads `...=False`; removing the loop itself (still honoring `Limit`) reads `...=True` instead — `backend/tests/test_dynamo_adapters.py::test_dynamo_component_repository_list_components_paginates_diagnostic_message_on_forced_truncation` and the mutation patch `docs/scrum/stories/STORY-213-ac2-mutation-remove-lek-loop.patch`. None of the five ASSERTIONS changed; every test above still requires the same full result. The fixture-race/absent-LEK hypothesis was probed (300 write-then-query and 200 delete-recreate-paginate iterations, 0 divergences either way) and recorded as a negative result, not fixed — see `STORY-213-pagination-test-isolation.md`. The one authoritative statement of which LEK value (plus page count) means what now lives solely in `PaginationSpy.diagnostic`'s docstring (`backend/tests/pagination_diagnostics.py`) — a fix-round pass found and removed a second copy that had the flake/regression mapping backwards, and it is deliberately not restated at any call site to avoid a second driftable copy.
- **`DynamoProposalRepository.record_approval_event` (STORY-200, ZR-6 fix — see [[zone-rules]]).**
  `action` is `ProposalState`, matching the port. The branch that denormalizes `approved_actor` onto
  the proposal's META item compares by ENUM IDENTITY (`action is ProposalState.APPROVED`), not a
  string literal. `.value` is used EXPLICITLY at both write sites — the `sk`
  (`f"EVENT#{occurred_at_str}#{action.value}"`) and the `"action"` item attribute — because
  `ProposalState` is `class ProposalState(str, Enum)`, a str MIXIN and not `StrEnum`, so on Python
  3.13 an f-string over the bare member renders `"ProposalState.APPROVED"`, not `"approved"`; using
  the bare member at the `sk` site silently corrupts every approval event's sort key (reproduced as
  an actual failing `get_item` lookup before the fix, and again via the AC7 mutation below — not
  reasoned about only). Proven ONLY against real DynamoDB Local by
  `test_dynamo_proposal_repository_record_approval_event`
  (`backend/tests/test_dynamo_proposal_repository.py`), which asserts BOTH halves: `approved_actor`
  IS written on approve and is NOT written on reject. `FakeProposalRepository.record_approval_event`
  (`backend/tests/fakes.py`) only appends a dict — it does not implement this denormalization at
  all — so this branch is unobservable through the fake; a fake-based test cannot substitute for the
  real-DynamoDB one. Mutation-proven: changing `ProposalState.APPROVED`'s VALUE (not its name) trips
  that same test (the sort key it looks up no longer exists); restored, `git diff` empty.
- `DynamoRejectedObservationRepository` implements the append-only quarantine sink under the `REJECTED#<signal_key|UNKNOWN>` partition with distinct uuid-suffixed SKs, converting payload floats to Decimal to satisfy boto3 serialization.
- **`topology_keys.py` (STORY-205, ZR-8 Finding 1 fix — see [[zone-rules]]).**
  `backend/src/adapters/persistence/topology_keys.py` is the single declaration of the
  `TOPOLOGY` partition's key schema, in both shapes it is consumed in: the item-key dict
  (`app_item_key`, `component_item_key`, `signal_item_key`, for `put_item`/
  `update_item`/`get_item`) and the boto3 query condition (`component_query_condition`,
  `signal_query_condition`, for `.query()`). `DynamoComponentRepository`,
  `DynamoSignalRepository` and `seed_topology_dynamo` all import from it rather than
  each re-declaring the schema — before this story, `seed_dynamo.py` hand-built the same
  `pk`/`sk` shape independently, a THIRD declaration on the boot path of both
  composition roots. Pinned by `backend/tests/test_topology_keys.py` (the two shapes,
  unit-level); the standing guard against a regression (AST-asserts `seed_dynamo.py`
  builds no `pk`/`sk` dict literal of its own) is documented in [[zone-rules]] (ZR-8).
- `seed_topology_dynamo` (`backend/src/composition/seed_dynamo.py`) idempotently upserts
  Git-configured apps, components, and signals into the `TOPOLOGY` partition, obtaining
  its keys from `topology_keys.py` (above). Uses an update expression with
  `if_not_exists` to preserve existing component status on re-seed.
- Contract parity is verified in `backend/tests/test_dynamo_adapters.py`, `backend/tests/test_dynamo_publication_repository.py`, `backend/tests/test_dynamo_maintenance_repository.py`, `backend/tests/test_dynamo_rejected_observation_repository.py`, and `backend/tests/test_dynamo_seed.py` against a real local DynamoDB instance.

### Testing convention

- Under `pytest`, the session-scoped `dynamo_local` fixture (via `dynamo_local.resolve_dynamo()`) spawns a throwaway DynamoDB Local container (or reuses `DYNAMO_ENDPOINT_URL`), and `clean_dynamo_tables` (function-scoped) deletes/re-creates tables for per-test isolation, supporting DynamoDB integration tests.

## Inference (synthesis, not verified)
- Eventual consistency of Global Secondary Indexes is mitigated by scheduling maintenance windows in advance, but could lead to race conditions if checked immediately after creation.

## History
- sprint-68 (STORY-205 fix round): RE-VERIFIED, no content change. The sweep flagged
  `topology_keys.py` and `test_topology_keys.py` (both `code_refs`) for the quality-review
  fix round's rename of the public `TOPOLOGY_PK` constant to `_TOPOLOGY_PK` (no consumer
  outside the module and its own unit test, confirmed by a whole-repo grep both before and
  after) and the sort fix + meta-test rename in `backend/tests/test_zone_layout.py` (also a
  `code_ref`). This article's Facts describe the key-schema module and its consumers at the
  function level (`app_item_key`, `component_item_key`, `signal_item_key`,
  `component_query_condition`, `signal_query_condition`) and never name the `TOPOLOGY_PK`
  constant itself, so no Fact is wrong. verified_sha -> d9a3f95.
- sprint-68 (STORY-205): landed the ZR-8 Finding 1 fix (see [[zone-rules]]). Added
  `topology_keys.py` to `code_refs` and its Fact above: the single declaration of the
  `TOPOLOGY` key schema in both consumed shapes, imported by `DynamoComponentRepository`,
  `DynamoSignalRepository` and `seed_topology_dynamo` (previously each declared it
  independently, `seed_dynamo.py` being the third and last to stop). **Fixed a stale
  citation while here**, per this story's AC7: the `seed_topology_dynamo` Fact cited
  `src/composition/seed_dynamo.py`, a path that does not resolve from the repo root
  (the tree is `backend/src/...`) — the Facts lint had been skipping that claim
  entirely; corrected to `backend/src/composition/seed_dynamo.py`. No other Fact in
  this article changed; `DynamoComponentRepository`/`DynamoSignalRepository`'s own
  behaviour is unchanged (proven by `test_dynamo_adapters.py` passing without
  modification), only where they obtain their keys from. verified_sha -> a5a2d68.
- sprint-67 (STORY-200): landed the ZR-6 fix (see [[zone-rules]]). Added the
  `DynamoProposalRepository.record_approval_event` Fact above: enum-identity comparison, explicit
  `.value` at both write sites, the real-DynamoDB proving test (`fakes.py` cannot observe this
  branch), and the AC7 mutation proof. `test_dynamo_proposal_repository.py`'s
  `test_dynamo_proposal_repository_orphan_event_guard` also needed updating (two `action="rejected"`
  call sites, not named by the story's own AC8 list, which named only the two `"approved"` sites) —
  the `.value` access on a bare `str` raises `AttributeError` rather than the expected `ClientError`,
  so every real-adapter caller of this method now passes `ProposalState`, not just the two AC8 named.
  `test_dynamo_publication_repository.py`'s author-parity test likewise updated. verified_sha ->
  d469d2c.
- sprint-67 (STORY-199 fix round, quality review): fixed a self-contradiction — the previous text
  said the proposal-repo files' "own code_refs live in [[zone-rules]], not here", while commit
  `15ea91c` had already added both to THIS article's `code_refs`. No Fact changed; the sentence now
  matches the front-matter. verified_sha -> fe8df72.
- sprint-67 (STORY-199): `list_components`, `list_windows`, `list_signals`, `is_under_maintenance` and
  `list_open` now loop on `LastEvaluatedKey` instead of silently truncating past a 1MB page — the
  live defect was `is_under_maintenance` returning a silent `False` for a component genuinely under
  maintenance. Added the "Pagination" Fact above. `is_under_maintenance` is boolean-short-circuiting,
  not collect-all: page until a match (return `True` immediately) or until `LastEvaluatedKey` is
  exhausted (return `False`); it never terminates on an empty-after-filter page. verified_sha ->
  460d3ee.
- sprint-63 (STORY-180): RE-VERIFIED, no content change. The sweep flagged `backend/tests/conftest.py`
  for STORY-180's `sys.path` insertion-position decision (minor 8, the `tools/` insertion recorded
  as a deliberate front-insertion with its reason) — the `dynamo_local`/`clean_dynamo_tables`
  fixture behaviour this article documents is byte-identical. verified_sha -> 701bfab.
- sprint-46 (STORY-082/083): Added DynamoDB topology adapters and serde logic with contract parity tests. verified_sha -> 5ddf3ab.
- sprint-48 (STORY-086): Added DynamoDB publication, maintenance, and rejected observation repositories, and seed_topology_dynamo, with full contract parity tests. verified_sha -> d710c8c.
- sprint-49 (STORY-087): Fully retired Neon Postgres database, Alembic migrations, and the nine Postgres repository adapters. Rewired composition and endpoints to DynamoDB Local.
- sprint-62 (STORY-146): RE-VERIFIED, no content change. Only `test_dynamo_seed.py`'s `AppConfig` construction changed; `seed_dynamo.py` itself is untouched (AC7) and its `for sig in app.signals:` loop reads the same derived list it always did. verified_sha -> d004da7.
- sprint-62 (STORY-148): RE-VERIFIED, no content change. The sweep flagged `backend/tests/conftest.py` in `code_refs` for a second `sys.path` insertion (repo-root `tools/`, alongside the existing `scripts/` one, so the new `tools/demo_engine/` Grail-shaped demo HTTP server is importable from tests). The `dynamo_local`/`clean_dynamo_tables` fixture behaviour this article documents is byte-identical. verified_sha -> ba00bd5.
