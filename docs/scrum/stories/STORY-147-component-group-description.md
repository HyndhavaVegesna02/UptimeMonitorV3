---
id: STORY-147
title: Component group + description — config to ComponentDTO
type: feature
points: 3          # RE-ESTIMATED 2 -> 3 at sprint-72 pre-lock verification: the diff necessarily
                   # reaches FIVE verified/map wiki articles, which A18 forces re-verified in-story.
status: ready
refined: 2026-07-28   # PO-approved at sprint-62 refinement; citations re-verified 2026-08-14 and
                      # again 2026-08-15 at sprint-73 pre-lock verification -- all rows exact.
sprint: 73   # story 1 of 3 -- PO ruling 2026-08-15 "i want 147". PENDING PO LOCK.
---

> ## *** IN SPRINT 73, STORY 1 OF 3 — PO ruling 2026-08-15: "i want 147". ***
>
> Sprint-73 v2 had cut it again (STORY-155b re-priced 5 → 7 pushed the sprint to 13) and put the
> choice to the PO — archive it, or commit it — because a third silent deferral is what produced
> STORY-186. The PO chose to commit it, and it runs **FIRST**: it is the only independent, already
> `ready`, small story in the sprint, and scheduling it last is what gets a story dropped.
>
> **Its citations were re-verified a THIRD time at sprint-73 pre-lock verification (2026-08-15) and
> every row of the table below is exact at HEAD** — `ComponentConfig` at `config.py:180`,
> `load_config` at `:567`, the bare-`ValueError` re-raise at `:650-651`, `component.py:22`, and
> `models.py:9-16` in a file that is exactly 16 lines. AC4 is structurally guaranteed:
> `adapters/outbound/statuspage/__init__.py:54` is `{"component": {"status": vendor_status}}`.
> Two citation corrections were applied at that verification: the wiki re-verification rule is
> `.scrum/definition-of-done.md:133-136` (not `:110-114`, which is STORY-224's self-test note), and
> the `if not isinstance(data, dict)` line is `:354-355`, not `:356`.

> **DEFERRED OUT OF SPRINT 72 (2026-08-14) on its own re-measurement, not on priority.** Pre-lock
> verification found the diff must touch `composition/config.py`, `composition/seed_dynamo.py`,
> `core/domain/component.py`, `adapters/persistence/dynamo_component_repository.py`,
> `api/v1/components/{models,service}.py`, `config/apps/httpcheck.yaml` and
> `backend/tests/fakes.py` — whose `code_refs` span **five `verified`/`tier: map` articles**:
> `config-layer.md` (417 lines), `zone-rules.md` (975), `canonical-types-and-ports.md` (312),
> `persistence-adapters.md` (143), `api-five-file-convention.md` (82).
> `.scrum/definition-of-done.md:133-136` requires each to be updated or re-verified **within the
> story**. That is the largest wiki radius in the candidate set and it was priced at zero. **The
> estimate is corrected to 3 here so it enters its next sprint honestly sized**, with the citation
> table below already re-derived. Sprint-73 candidate.

## Context

The PO-approved reference UI shows every component with a category chip
(`COMMERCE` / `PLATFORM` / `DATA` / `DISCOVERY` / `MESSAGING`) and a one-line description
("Cart, payments and order placement"). Neither exists anywhere in the system: `ComponentDTO`
carries only `id`, `name`, `status` (`backend/src/api/v1/components/models.py:14-16`; `:12` is the
`model_config` line).

These are the two cheapest items in the whole UI gap analysis and they unblock visuals on
every page (see `ui-backend-gap-analysis.md` §2.1/§2.2, item B4). Sequencing matters: whoever
adds the coming components is already authoring `id`/`name`/`statuspage_component_id`, so if
the schema has these fields they get filled in the same edit rather than every entry being
edited twice. That is why this lands before the fleet expansion.

## Description

Add two optional fields to a component's config declaration and carry them through the
existing vertical slice to the HTTP surface:

```
ComponentConfig      → seed (persist on the COMPONENT# item)
  → Component        → Dynamo component repository (read back)
  → ComponentDTO     → GET /api/v1/components
```

### *** CITATIONS RE-VERIFIED 2026-08-14 at sprint-72 planning (HEAD `fa5507d`) ***

This story was written at sprint-62 planning and STORY-146 has since reshaped `config.py`. **Use
this table; the line numbers written elsewhere in this file are from 2026-07-28.**

| Written in this story | Actually, at `fa5507d` |
| --- | --- |
| `ComponentConfig` at `composition/config.py:57` | **`backend/src/composition/config.py:180`** (`model_config = ConfigDict(frozen=True)`, `id`/`name`/`monitors`) |
| the `try/except (TypeError, ValueError)` at `config.py:343-357` | **`load_config` is `config.py:567`; the `except (TypeError, ValueError)` → bare `ValueError(f"Invalid config in {yaml_path.name}: …")` is `config.py:650-651`** |
| `seed_dynamo.py:42` | **`backend/src/composition/seed_dynamo.py:41-56`** — the components `update_item` with `if_not_exists` on status |
| `Component` at `core/domain/component.py:22` | **unchanged — `:22`** ✔ |
| `ComponentDTO` at `api/v1/components/models.py:9-16` | **unchanged — `:9-16`, and the file is exactly 16 lines** ✔ |

**AC1's pattern is no longer novel — it is now the established idiom in this file, which is what
retires the risk that sank this story's first draft.** `config.py:589-594` documents it in prose:
*"The last four checks run OUTSIDE the `except (TypeError, ValueError)` block below, so their named
subclasses (all `ConfigError`) survive to the caller — a pydantic `model_validator` cannot do this
(probed twice, independently)."* The `ConfigError` hierarchy AC1 depends on exists at
`config.py:97-123` (`ConfigError`, plus `FlatSignalsRejectedError`, `UndeclaredLocationAliasError`,
`InvalidFreshnessError`, `DuplicateAppIdError`). **STORY-146 is `done`**, so AC1's stated dependency
is discharged; add `InvalidComponentFieldError` alongside those.

Normal dependency direction; no boundary risk.

`group` is **free text normalized to a slug at load**, not a closed enum: a closed enum would
make every new category a code change and a deploy, which fights dossier §4 (editing config is
a topology change, not a code change). Slug normalization is what stops
`Platform`/`platform`/`PLATFORM` forking into three phantom groups, and it means promoting
`group` from a decorative label to grid sections or a filter later is a pure frontend change
with no stored-data cleanup.

`group` is **decorative in this story** — a display sub-label only. Sectioning the dashboard
by group is deliberately deferred: with one component it would render five headings and four
empty sections, and whether "group" is even the right axis to cut a 30-component fleet needs
real cards on screen to judge (PO discussion 2026-07-28).

## Acceptance Criteria

- [ ] **AC1** — `ComponentConfig` accepts optional `group` and `description`. A `group` that is
      not slug-safe after normalization, or a `description` longer than 80 characters, raises
      `InvalidComponentFieldError` (a `ConfigError`/`ValueError` subclass — the hierarchy
      STORY-146 landed at `config.py:97-123`) naming the offending component and field — never a
      bare `ValueError`, and never silent truncation. **The check runs in `load_config`
      (`config.py:567`) OUTSIDE the `try/except (TypeError, ValueError)` at `config.py:650-651`**:
      verified by probe, a `ValueError` subclass raised inside a pydantic `model_validator` is
      converted to `ValidationError` (losing the subclass), which `config.py:651` then re-raises as
      a bare `ValueError(f"Invalid config in {yaml_path.name}: …")`. A validator-based
      implementation cannot satisfy this AC. The test asserts the specific class, not `ValueError`.
      ⚠ **The citations `config.py:343-357` / `:356` that stood here until 2026-08-14 were stale in
      the worst possible direction: `:343-357` is now `AppConfig`'s `mode="before"`
      `model_validator` — the exact implementation this AC forbids — and the `if not isinstance(data, dict): return data`
      line is `:354-355`, not `:356` (which is blank) — corrected at sprint-73 verification.** Caught at pre-lock verification. Follow the
      line numbers in this paragraph and the table above, not any others in this file.
- [ ] **AC2** — `group` is normalized to a lowercase slug at load: `Commerce`, `COMMERCE`, and
      `commerce` all load as `commerce`. A test asserts all three inputs produce one value.
      Display-casing is the frontend's concern, not config's.
- [ ] **AC3** — ⚠ *Implementation note from pre-lock verification: the round-trip is shaped as this
      story assumes (`seed_dynamo.py:41-56` → `dynamo_component_repository.py:24-30` `_map_item` →
      `ComponentsService.get_all_components` → `ComponentDTO`), but `_map_item` reads with **bracket
      access** (`item["name"]`), so the two new fields must be read with `.get()` or every
      already-seeded item raises `KeyError` on read-back.* Both fields round-trip config → seed →
      repository → DTO, and
      `GET /api/v1/components` returns them. When absent they serialize as **`null`** — never
      `""` and never a placeholder like `"Uncategorized"`. A component with no `group` is a
      legitimate state (a newly added component exists before anyone categorizes it), and the
      UI omits the chip rather than printing filler.
- [ ] **AC4** — **Neither field reaches Statuspage.** These are internal operator-cockpit
      metadata; Statuspage owns its own component naming. A test asserts the Statuspage
      publish payload and `statuspage_mapping()` are byte-identical to before this story.
- [ ] **AC5** — Existing `ComponentDTO` consumers are unaffected: the two added fields are
      additive and optional, and every existing components-endpoint test passes untouched.
- [ ] **AC6** — All five backend DoD gate commands exit 0.

## Open Questions

None.

## History

- 2026-07-28: drafted. PO decisions taken in discussion: internal-only (not published to
  Statuspage), free text slug-normalized rather than a closed enum, decorative not structural
  for now, both optional with the chip omitted when absent, `description` length-capped and
  validated where it is authored. Recorded in
  `docs/scrum/sprints/2026-07-28-sprint-62/ui-backend-gap-analysis.md` §3a.
- 2026-07-28: **amended and DEFERRED out of sprint 62 after `yt-plan-verifier` (pre-lock).**
  Two changes. (1) AC1's "named error" was unsatisfiable as specified — the same pydantic
  conversion issue found in STORY-146 — so AC1 now names `InvalidComponentFieldError` and pins
  where it is raised; it also now depends on the `ConfigError` hierarchy STORY-146 introduces,
  which is a further reason to sequence it after that story rather than beside it.
  (2) Deferred to **sprint 63**, where the frontend that consumes these fields lands. Both
  fields are purely decorative with **no consumer until then** (`group` is explicitly a display
  sub-label, AC-level: "decorative in this story"), so landing them a sprint earlier buys
  nothing, while deferring keeps sprint 62 at ~10 pts with real verification headroom on the
  demo-engine work. This matches the PO's standing pacing directive ("do it multi sprint, with
  carefull verification, no need to rush in single stretch"). Verified as safe to defer: the
  verifier confirmed AC4 is *structurally* guaranteed — the Statuspage payload is
  `{"component": {"status": …}}` (`adapters/outbound/statuspage/__init__.py:54`), so neither
  field can leak regardless of when this lands. Citation fix: `ComponentDTO` is
  `api/v1/components/models.py:9-16` (the file is 16 lines; the earlier `:12-19` overran it — and
  the first correction to `:9-17` overran it by one, caught by the second verifier pass).
- 2026-07-28: second verifier pass — AC2 normalizes `group` inside the model while AC1 validates
  it, and the same pydantic trap applies: a `ValueError` subclass raised in a validator becomes
  `ValidationError`. Normalization may live in the model; the **validation** must be in
  `load_config` outside the `try` at `config.py:343-357`, per AC1.
