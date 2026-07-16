---
title: Persistence adapters — the repository implementations
code_refs: [backend/tests/test_component_repository_contract.py, backend/tests/test_signal_repository_contract.py, backend/src/core/queries/availability.py, backend/tests/conftest.py, backend/tests/fakes.py, backend/src/adapters/persistence/dynamo_signal_repository.py, backend/src/adapters/persistence/dynamo_component_repository.py, backend/src/adapters/persistence/dynamo_watermark_repository.py, backend/src/adapters/persistence/dynamo_sample_mode_repository.py, backend/src/adapters/persistence/dynamo_serde.py, backend/tests/test_dynamo_adapters.py, backend/src/adapters/persistence/dynamo_publication_repository.py, backend/src/adapters/persistence/dynamo_maintenance_repository.py, backend/src/adapters/persistence/dynamo_rejected_observation_repository.py, backend/src/composition/seed_dynamo.py, backend/tests/test_dynamo_publication_repository.py, backend/tests/test_dynamo_maintenance_repository.py, backend/tests/test_dynamo_rejected_observation_repository.py, backend/tests/test_dynamo_seed.py]
verified_sha: 632a302c8d86065ae6216d8b18eb299fd481dc12
verified_sprint: sprint-49
status: verified
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
- `DynamoRejectedObservationRepository` implements the append-only quarantine sink under the `REJECTED#<signal_key|UNKNOWN>` partition with distinct uuid-suffixed SKs, converting payload floats to Decimal to satisfy boto3 serialization.
- `seed_topology_dynamo` (`src/composition/seed_dynamo.py`) idempotently upserts Git-configured apps, components, and signals into the `TOPOLOGY` partition. Uses an update expression with `if_not_exists` to preserve existing component status on re-seed.
- Contract parity is verified in `backend/tests/test_dynamo_adapters.py`, `backend/tests/test_dynamo_publication_repository.py`, `backend/tests/test_dynamo_maintenance_repository.py`, `backend/tests/test_dynamo_rejected_observation_repository.py`, and `backend/tests/test_dynamo_seed.py` against a real local DynamoDB instance.

### Testing convention

- Under `pytest`, the session-scoped `dynamo_local` fixture (via `dynamo_local.resolve_dynamo()`) spawns a throwaway DynamoDB Local container (or reuses `DYNAMO_ENDPOINT_URL`), and `clean_dynamo_tables` (function-scoped) deletes/re-creates tables for per-test isolation, supporting DynamoDB integration tests.

## Inference (synthesis, not verified)
- Eventual consistency of Global Secondary Indexes is mitigated by scheduling maintenance windows in advance, but could lead to race conditions if checked immediately after creation.

## History
- sprint-46 (STORY-082/083): Added DynamoDB topology adapters and serde logic with contract parity tests. verified_sha -> 5ddf3ab.
- sprint-48 (STORY-086): Added DynamoDB publication, maintenance, and rejected observation repositories, and seed_topology_dynamo, with full contract parity tests. verified_sha -> d710c8c.
- sprint-49 (STORY-087): Fully retired Neon Postgres database, Alembic migrations, and the nine Postgres repository adapters. Rewired composition and endpoints to DynamoDB Local.
