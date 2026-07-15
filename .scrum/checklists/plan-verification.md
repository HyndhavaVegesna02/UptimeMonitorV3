# Plan Verification Checklist (pre-lock) — Uptime Monitor V3

> YourTeam v2. Run by yt-plan-verifier once per sprint, after plan.md is drafted, BEFORE the
> PO is asked to lock. Migration map PO-approved 2026-07-12 — this checklist is the BINDING
> home for these items; dates cite the original motivating agreement (full text in git history).

## Contract precision (consumer stories)

- [ ] Every DTO field an AC names exists on the producing model (`backend/src/api/v1/<feature>/models.py`); a missing field is trimmed from the AC or split into a producer story — never locked unsatisfiable (2026-07-02).
- [ ] Every numeric field's scale/units read from the PRODUCING code (service/domain computation) and stated in the plan's "Verified API contracts" section — never inferred from the field name; `_pct` once meant a 0–1 fraction (2026-07-04, sprint 32).
- [ ] Every string field's enum/format verified against the producer.
- [ ] Every claimed producer gap (missing 422, absent behavior) proven by a live probe of the failure path actually failing, or by the producer's own test driving that exact case — never inferred from one validation layer (2026-07-06, sprint 34's false defect).

## Specification completeness

- [ ] Every port/repository method the plan specifies states not-found / wrong-state / conflict / empty behavior explicitly — raise which named error vs return what (2026-06-26).
- [ ] Every new fixture names its real-sample source (live capture or producer fixtures) (2026-07-04).
- [ ] Breakdown↔AC trace: every AC is covered by plan steps; no step contradicts an AC.
- [ ] AC do not pre-declare wiki blast radius — the mechanical sweep is the sole decider (2026-07-03).
- [ ] Any live-verification AC has an in-sprint execution plan, or the story is flagged to split (2026-06-29).
- [ ] Vendor-resource ids the sprint adds/changes have a planned resolves-to-live-data probe (2026-07-08).

## External mode only

- [ ] plan.md is fully self-contained: the conventions checklist is embedded; every step introducing a new module/public symbol names its docstring deliverable; the external implementer builds literally and infers nothing (2026-06-27).
- [ ] Any concrete vendor mechanism the plan prescribes LITERALLY — a specific condition
      expression, key shape, transaction item, or API-call form — is checked for FEASIBILITY
      against the vendor's actual semantics, not just for presence. An infeasible literal
      instruction is a GAP even when the intent is right: in external mode a literal agent
      implements the broken form (2026-07-15; sprint-48 STORY-091 AC1 — the plan told the
      agent to add `attribute_exists(pk)` to the event Put, but on a create the item's own
      key does not exist yet so it fails every happy-path write; the agent silently corrected
      it to a ConditionCheck-on-META, and the plan-verifier had passed it by checking only
      "is a guard specified?").

## Preconditions

- [ ] Clean working tree and green DoD baseline on main stated as verified (edge-case #1).
- [ ] Execution mode declared in the plan (`mode:` in sprint-current.yaml).
- [ ] Scope within a single focused session's shape; dependencies ordered first, risk early.
