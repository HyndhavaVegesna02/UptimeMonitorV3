# Plan Verification Checklist (pre-lock) — <PROJECT>

> YourTeam v2 template (yourteam_version: 2.0.0). Run by yt-plan-verifier once per sprint,
> after plan.md is drafted, BEFORE the PO is asked to lock.

## Contract precision (consumer stories)

- [ ] Every field an AC names exists on the producing contract (model/schema/DTO); a missing field is trimmed or split into a producer story — never locked unsatisfiable.
- [ ] Every numeric field's scale/units read from the PRODUCING code and stated in the plan — never inferred from the field name (a `_pct` field was once a 0–1 fraction; the wrong scale survived 146 green tests).
- [ ] Every string field's enum/format verified against the producer.
- [ ] Every claimed producer gap proven by a live probe of the failure path actually failing, or by the producer's own test driving that exact case — never inferred from reading one layer.

## Specification completeness

- [ ] Every port/repository method the plan specifies states not-found / wrong-state / conflict / empty behavior explicitly.
- [ ] Every new fixture names its real-sample source.
- [ ] Breakdown↔AC trace: every AC covered by plan steps; no step contradicts an AC.
- [ ] AC do not pre-declare wiki blast radius — the mechanical sweep decides.
- [ ] Any live-verification AC has an in-sprint execution plan, or the story is flagged to split.
- [ ] Vendor-resource ids the sprint adds/changes have a planned resolves-to-live-data probe.

## External mode only

- [ ] plan.md is fully self-contained: conventions checklist embedded; docstring deliverables named per new module/public symbol; the external implementer builds literally and infers nothing.

## Preconditions

- [ ] Clean working tree and green DoD baseline on main stated as verified.
- [ ] Execution mode declared.
- [ ] Scope within a single focused session's shape; dependencies ordered first, risk early.

## Project additions (this project)

<!-- Seeded empty at inception; grows via retro routing. -->
