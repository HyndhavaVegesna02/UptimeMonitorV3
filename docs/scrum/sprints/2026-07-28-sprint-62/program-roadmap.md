# Program roadmap — new UI + fleet readiness

**Date:** 2026-07-28. PO chose scope option **(a)** (UI-first after the demo engine) and
directed: *"do it multi sprint, with carefull verification, no need to rush in single
stretch."* So option (a)'s ~21 points are **split across sprints** rather than crammed into
one. Target size ≈ 10 points per sprint (the ~9 baseline noted at sprint-61 planning).

Only **sprint 62 is planned**. Everything after it is a sketch, re-planned at each planning
ceremony as YourTeam requires — listed here so the sequencing logic is visible, not to
pre-commit scope.

---

## Sprint 62 — "the fleet exists, and it flows" (10 pts)

**Goal:** a scripted multi-component / multi-signal / multi-location fleet flowing through
the **real** pipeline into DynamoDB, and the existing API returning fleet-scale data for the
first time. No frontend work.

*Revised 2026-07-28 after `yt-plan-verifier` (verdict GAPS): the demo engine is split in two,
and `group`/`description` moves to sprint 63 where its consuming frontend lands. Total
programme scope is unchanged — see `plan.md` "Verifier pass".*

| Story | Est | Why here |
| ----- | --- | -------- |
| **STORY-146 · Config reshape** — nested `monitors:` under components, `locations:` block, `freshness:` block | 3 | The authoring shape everything downstream reads; lands before the fleet grows so entries are authored once. Highest blast radius (8 consumers of `app.signals`) |
| **STORY-148 · Demo engine pt 1** — the wire contract: 7-field rows at real scale, **both** DQL grammars, the async Grail HTTP protocol, proven through the real executor | 3 | Fidelity is the whole value of D4 option (b), and three separate code paths return *silently empty* when it is wrong — so it is verified on its own before anything is built on it |
| **STORY-176 · Demo engine pt 2** — scenario player, ≥12-component demo fleet, config-only publish guard, real loop run | 3 | Consumes 146's shape and 148's engine; this is the story that makes the fleet real |
| **STORY-149 · P1** — `degraded` streak check in `anti_flap` | 1 | 4 lines, closes the no-damping defect, no modelling debate |
| ~~`group` + `description` (B4)~~ | ~~2~~ | **Deferred to sprint 63** — purely decorative with no consumer until the frontend, and it now depends on the `ConfigError` hierarchy STORY-146 introduces |

**Demo:** point `DYNATRACE_ENV_URL` at the demo engine, run the real loop, and show 12
components / ~50 signals / 4 locations landing in DynamoDB — then every existing `/api/v1`
endpoint returning genuinely multi-component data. Show a scripted degradation crossing the
anti-flap ladder and opening a proposal.

**Verification notes:** the demo engine's fidelity to the Dynatrace wire shape is the whole
value, so its reality gate is a **byte-shape comparison against the real captured fixtures**
(`backend/tests/fixtures/dynatrace/grail_synthetic_events.json` etc.), not just "the loop
didn't crash". The publisher **must** be stubbed or pointed at a throwaway Statuspage page
before the loop runs (D4 constraint 1).

**Explicitly NOT in scope:** P2 breadth model, Option B per-component loop, any frontend.

---

## Sprint 63 (sketch) — "the visual language, approved before it multiplies" (≈8–10)

Design system ported from the reference (tokens, glass surfaces, dark inset sidebar,
Manrope/JetBrains Mono, teal 4-status ramp + the maintenance chip), plus the app shell
(sidebar, topbar, routing, **responsive at 390** — the reference has none).

Ends with a **PO look-and-feel checkpoint** on the styleguide + shell, *before* six pages
are built on the language. This is the pilot fix for the process failure behind three
rejections (see `sprint-61/aborted.md`): every rejection came after a full build, because
nothing in the loop verified "the PO wants this look" until a sprint's work existed.

## Sprint 64 (sketch) — "the Dashboard, on real fleet-scale data" (≈10)

The Dashboard against the demo-engine fleet. Three of four KPIs are already free from
existing endpoints; only fleet uptime needs aggregation, so **B1 (fleet summary) is deferred
until the N+1 actually hurts** rather than blocking the page on a new endpoint.

## Sprint 65+ (sketch)

- **Availability + Check History** — needs B2 (fleet history: optional `signal_key`,
  filters, offset, total count) and B3 (bucketed series for sparklines / 30-block bars).
- **Approvals + Maintenance + Publications** — needs B8 (populate `StatusProposal.reason`
  at open time; the field already exists and is load-bearing for D2).
- **Pipeline correctness before the fleet expands** — P2 breadth ceiling (D1/D2), Option B
  per-component decision loop, freshness/re-entry, F1 rejection suppression. **Not urgent
  (they only bite with multiple monitors per component, which doesn't exist yet) but
  prerequisite to the real fleet expansion.** Whenever that expansion gets scheduled, this
  lands first.
- **Renew Dynatrace → map the real failure codes** and re-verify every assumption the demo
  engine baked in (D4 constraint 2).

---

## Still open (not blocking sprint 62)

| # | Question | Blocks |
| - | -------- | ------ |
| 1 | **Rebuild base** — branch from `main` + cherry-pick sprint-61's design-neutral infra (`api/`, `useFetch`, `fetchDedup`, pure helpers, MSW harness), fully clean, or from the sprint-61 tip? Recommendation: cherry-pick, under the rule *"if it renders, rebuild it; if it's data→data, keep it."* | sprint 63 |
| 2 | **Check History result taxonomy** — the reference's `Success / Slow / Timeout / Failure` vs our `up / down / degraded`. Relabel the design, or add latency-threshold "slow" and a timeout distinction to the domain? | sprint 65 |
| 3 | **Actor on an approval** — `POST /decisions/{id}` needs an `actor` for the audit trail; the reference hardcodes "Nadia M."; there are no users in the backend. Build-time name, operator-typed field, or real auth? | the Approvals sprint |
| 4 | **Real Dynatrace location ids + names** for the `locations:` block, and aliases that match Dynatrace's own vocabulary. | Resolved for sprint 62: aliases are short non-cloud-provider names, and the migrated **live** config gets no `locations:` block at all (STORY-146 AC8) — fabricated vendor ids stay in demo config only. Real values still need trial renewal |

Decided already and recorded: `ui-backend-gap-analysis.md` §3a (fleet density, palette,
confidence %, `group`/`description`, publication deferral, multi-component drop) and
`decisions-and-future-work.md` D1–D4, F1–F3.
