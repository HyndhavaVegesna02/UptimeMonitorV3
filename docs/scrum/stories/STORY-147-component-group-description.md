---
id: STORY-147
title: Component group + description — config to ComponentDTO
type: feature
---

## Context

The PO-approved reference UI shows every component with a category chip
(`COMMERCE` / `PLATFORM` / `DATA` / `DISCOVERY` / `MESSAGING`) and a one-line description
("Cart, payments and order placement"). Neither exists anywhere in the system: `ComponentDTO`
carries only `id`, `name`, `status` (`backend/src/api/v1/components/models.py:12`).

These are the two cheapest items in the whole UI gap analysis and they unblock visuals on
every page (see `ui-backend-gap-analysis.md` §2.1/§2.2, item B4). Sequencing matters: whoever
adds the coming components is already authoring `id`/`name`/`statuspage_component_id`, so if
the schema has these fields they get filled in the same edit rather than every entry being
edited twice. That is why this lands before the fleet expansion.

## Description

Add two optional fields to a component's config declaration and carry them through the
existing vertical slice to the HTTP surface:

```
ComponentConfig (composition/config.py:57)
  → seed_dynamo.py:42  (persist on the COMPONENT# item)
  → Component          (core/domain/component.py:22)
  → Dynamo component repository (read back)
  → ComponentDTO       (api/v1/components/models.py:12)
```

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
      STORY-146 AC5 introduces) naming the offending component and field — never a bare
      `ValueError`, and never silent truncation. **The check runs in `load_config` OUTSIDE the
      `try/except (TypeError, ValueError)` at `config.py:343-357`**: verified by probe, a
      `ValueError` subclass raised inside a pydantic `model_validator` is converted to
      `ValidationError` (losing the subclass), which `config.py:356` then re-raises as a bare
      `ValueError(f"Invalid config in {file}: …")`. A validator-based implementation cannot
      satisfy this AC. The test asserts the specific class, not `ValueError`.
- [ ] **AC2** — `group` is normalized to a lowercase slug at load: `Commerce`, `COMMERCE`, and
      `commerce` all load as `commerce`. A test asserts all three inputs produce one value.
      Display-casing is the frontend's concern, not config's.
- [ ] **AC3** — Both fields round-trip config → seed → repository → DTO, and
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
