# Sprint 16 — Review

**Goal:** Build the config layer (dossier §7 Option C) — `config/apps/*.yaml` + a fail-fast
loader/validator + in-memory resolvers (`signal_key→component_id`, `component→AntiFlapThresholds`) —
the prerequisite that unblocks the pipeline orchestration.

**Branch:** `sprint-16` (from `sprint-16-start` @ `c797bb3`) · **HEAD:** `93f1863` (+ compile-pass commit)
**Committed:** 5 pts · **Story:** STORY-040a — Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **357 passed** (26 new config tests) |
| `lint-imports` | **5 kept, 0 broken** (config loader in composition; no new contract) |
| `check_fk_direction.py` | 0 violations |
| `alembic upgrade head` | exit 0 (no new migration) |
| `ruff check` / `format --check` | clean (128 files) |

Implemented by a **Sonnet implementer subagent** (PO's external quota), then verified + reviewed by
the orchestrator.

---

## STORY-040a — Config layer (5 pts)

`backend/src/composition/config.py` — frozen pydantic config models (`ComponentConfig`, `SignalConfig`,
`AppConfig`, `Config`), `load_config()` (reads `config/apps/*.yaml` via `yaml.safe_load`, fail-fast),
and the two resolvers (`component_for_signal` → `UnknownSignalError`; `thresholds_for` →
`UnknownComponentError`, §10 defaults `5/3/2/2`). Sample `config/apps/sockshop.yaml`. `pyyaml` added.

| AC | Verdict |
| --- | --- |
| AC1 load + resolve happy path (+ §10 default thresholds) | MET |
| AC2 fail-fast validation (6 cases: malformed YAML / missing field / undeclared component / dup signal_key / dup component.id / non-positive threshold) | MET |
| AC3 resolver unknown-key → named errors (not leaked `KeyError`) | MET |
| AC4 boundary (composition-zone; core imports nothing from it; 5/0) | MET |
| AC5 full gate + blast radius | MET |

- **Opus spec reviewer: PASS** (all five AC MET; every fail-fast case tested; §10-default path tested).
- **Opus quality reviewer: APPROVE** (0 critical / 0 major; `yaml.safe_load` confirmed — no unsafe
  deserialization; the `model_validator` genuinely fires on each invalid shape; cross-app global
  uniqueness is real and tested; minimal scope — no speculative publishing/SLA/gap config).

**First pass clean — no fix loop.** (The named errors subclass `ValueError`, the correct choice — a
`KeyError` subclass would be caught by `except KeyError`, the exact leak AC3 forbids.)

### Non-blocking minors (→ retro / follow-up)
1. `config.py` — malformed component/signal **sub-entries** are built before the `try/except`, so they
   miss the `"Invalid config in {filename}"` wrapper (still fail-fast; pydantic names the field).
2. The loader globs `*.yaml` only (not `*.yml`) — matches convention.
3. A few tests use broad `pytest.raises(Exception)`; could narrow to the named errors.

### Compile-pass note
The implementer seeded `config-layer.md` and re-verified `dev-setup-and-dod.md` for the `pyyaml` dep,
but missed that `api-five-file-convention.md` + `architecture-boundary.md` also carry `pyproject.toml`
in their `code_refs` (stale on the dep add — Facts unchanged). The orchestrator bumped those at the
compile pass and normalized `config-layer.md`'s `code_refs` to the project's inline `[...]` style.

---

## PO verdicts requested
**accept** (merge to main) or **reject**. STORY-040a passed the gate + both Opus reviewers first pass.
The three minors can fold into the accept (a small Sonnet/inline fix) or become a follow-up note.

## Next
With the config resolvers in place, **STORY-016a (pipeline orchestration)** is unblocked — the natural
Sprint 17 centerpiece. STORY-040 (the DB topology seed + signal→component migration) is independent.
