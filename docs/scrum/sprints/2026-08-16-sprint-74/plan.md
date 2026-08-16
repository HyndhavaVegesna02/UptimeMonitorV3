# Sprint 74 — Plan

**Status: VERIFIED, awaiting PO lock.** Pre-lock verification ran and all findings are applied
(see the bottom section). Both PO questions raised at planning — STORY-226's two rulings and
STORY-228's `Icon` registry question — have been answered and are written into the AC.

## Goal

> **Pay the review debt, then leave the enforcement machinery more honest than we found it.**

This sprint is scoped by direct PO instruction given at the sprint-73 close: *"in next sprint first
finish the minors then go to equilibrium list."* Every story here is a sprint-73 carried minor. The
equilibrium backlog is deliberately **not** in scope — it is what sprint 75 returns to.

## Scope — 4 stories, 15 points *(12 as first drafted; +3 from verification's re-pricing)*

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-228** — four documentation leftovers | 2 | `ready`, 6 AC, **PO ruled on AC4: REMOVE** |
| 2 | **STORY-229** — rehabilitate (or retire) `frontend-zone.md` | 5 | `ready`, 6 AC |
| 3 | **STORY-226** — ComponentConfig validation ergonomics | **3** *(was 2)* | `ready`, 7 AC, **both PO questions answered** |
| 4 | **STORY-227** — six test-pinning gaps | **5** *(was 3)* | `ready`, 7 AC |

STORY-228 was held out at verification because AC4 rested on an unanswered question — an open
question fails the Definition of Ready. **The PO answered it at planning (remove the four unused
`Icon` glyphs), so it is now `ready` and back in.**

### ⚠ 15 points is TWO ABOVE the highest this team has ever delivered

Velocity: 11, 10, 11, 11, 10, 8, **13**. This commits **15**. Stated at lock, not discovered at
review — the same disclosure sprint 73 made when it committed 13 against a best of 11, and that one
landed only after a mid-sprint pause on the session window.

**The mitigation is structural, and it is real this time.** Sprint 73's bad outcome was
*"delivers 3 instead of 13"* because its drop unit was a 10-point atomic pair. Here there is **no
atomic pair**: all four stories are mutually independent, so the drop unit is a single story.
**STORY-227 (5) is the declared first drop** — pure test-quality cleanup with no consumer waiting on
it. Read this as **10 points firm + 5 stretch**, not 15 committed evenly.

### Two stories were re-priced, and the reason indicts the first draft

**STORY-227: 3 → 5. STORY-226: 2 → 3.** Both for the same thing: **the draft priced wiki cost at
zero.** Measured at verification, 227's diff touches `code_refs` of **four** `tier: map` /
`status: verified` articles (`zone-rules`, `persistence-adapters`, `ingest-service-and-pull-loop`,
`statuspage-publish`) and its AC3 *mandates* an edit to `persistence-adapters.md`'s own Fact; 226's
diff stales `config-layer.md`. A18 and `.scrum/definition-of-done.md:133-136` force every one of
those updated or re-verified **in-story** — it cannot be deferred.

This is the same asymmetry sprint 73 caught when STORY-155b went 5 → 7, and its retro named the
correction as the thing to keep. Applying it here costs 3 points of apparent capacity and buys an
estimate that is true.

### The one structural improvement over sprint 73

**There is no atomic pair in this sprint.** All four stories are mutually independent: none blocks
another, and dropping any one leaves the rest coherent and shippable. That is what makes the
15-point commitment defensible — see the disclosure above — and it is a deliberate property of the
scope, not luck.

The one genuine coupling (228's `Icon.tsx` edit vs 229's article) is resolved by **ordering**, not by
an atomicity rule: run 228 first and it cannot fire.

## Execution order — 228 → 229 → 226 → 227

**228 first, and this ordering is a HAZARD FIX, not a preference.** The PO's ruling on AC4 — remove
the four unused glyphs — edits `frontend/src/components/Icon/Icon.tsx`, which is **`code_ref` #23 of
`frontend-zone.md`**, the article STORY-229 exists to fix. If 229 landed option (a) and set
`status: verified` first, this edit would re-stale that article at final HEAD (`yt_wiki.py:201-225`
diffs `code_refs` from the article's own last commit) — **silently undoing the sprint's 5-point
centrepiece**. Running 228 first removes the hazard by construction rather than by remembering to
handle it. It is also the smallest story, so the ordering costs nothing.

**229 second, because it carries all the uncertainty.** Its AC1 is a *decision* — rehabilitate as
`tier: map`, demote to `tier: reference`, or archive — and the three branches have materially
different costs. Running it early means we learn which branch we are on while there is capacity to
absorb the answer. It is also the only story that can grow: if the Fact-by-Fact pass exceeds the
estimate, its own AC says **stop and split rather than skimp**, and that call is far cheaper to make
in the first third of a sprint than the last.

**226 third, because it is the only behaviour change and the PO has already ruled on it.** Banking
it early follows sprint 73's lesson — a story scheduled last is a story that gets dropped, which is
the mechanism that produced STORY-186 across three sprints.

**227 last, because it is the safest thing to lose.** Pure test-quality cleanup with no consumer
waiting on it. It is tied-largest at 5, so losing it costs more than the first draft implied — that is the honest consequence of pricing it correctly, and it is visible here rather than
at review.

## Execution mode

`in-process`. Implementer → spec reviewer ∥ quality reviewer (concurrent) → mechanical gate →
reality gate, for every story (all are 2+ points; the 3+ rule catches 227 and 229, and sprint 73
showed the review pair earning its cost on every single story, so the 2-pointers get it too).

## Why the plan verifier WAS dispatched, despite this being an "internal" sprint

The token-economy rule says purely internal sprints — docs, one-zone refactors, UI against existing
DTOs — skip the pre-lock verifier, and note the skip. By the letter of the rule this sprint
qualifies for a skip: no adapter, no vendor path, no units/scale logic, no external mode.

**Dispatched, and the reason was specific.** Three of these four stories edit the
**enforcement machinery itself** — `test_citation_gate.py`'s baseline and article counts (229 AC5),
the route-table pin (227 AC1), the wiki tier system (229 AC1/AC4). Sprint 73's verifier found **four
CRITICALs, every one of which would have reddened the gate at a story's final commit**, and two of
them (C2, C4) were in exactly this machinery. A sprint that edits the thing that catches mistakes is
the last place to economise on checking.

## Risks, stated at planning rather than discovered at review

1. **STORY-229's AC1 may choose the expensive branch.** Rehabilitating as `tier: map` means the
   Fact-by-Fact pass — measured at verification as **25 bullets carrying 58 distinct citations, 33
   of them needing re-rooting**. If that overruns, the AC requires splitting, **not** skimping: a
   half-verified article restored to `status: verified` is strictly worse than the quarantined
   article we have today, because it converts visibly-stale into trusted-and-wrong.
2. **EVERY branch of STORY-229 moves the citation-gate numbers — not just archiving.** The draft
   plan asserted that options (a) and (b) did not; **verification disproved that by execution** —
   option (b) alone reds two assertions. AC5 now names all eight sites plus the prose.
   **Re-derive live; carry no figure from any document, including this plan.**
3. **STORY-226's authored-value plumbing has a documented trap — and a verified way through.** The
   obvious fix, moving the check into the pydantic validator, is the exact failure STORY-147
   documented twice: a `ValueError` subclass raised inside a validator becomes a `ValidationError`
   and loses its type. The check **must** stay in `load_config`, outside the `try/except`.
   Verification found the legitimate route: `raw` is assigned at `config.py:669-671` and is still in
   scope at the `:755` raise site — join on `comp.id`, never on list position.
4. **227's wiki radius is now the story's dominant cost, not its test edits.** Four `verified` map
   articles, one of them (`persistence-adapters.md`) carrying a mandated Fact edit. That is why it
   is a 5, and why it is last: if the sprint runs short, this is the honest thing to drop.
5. **`python -m pytest` must run from the REPO ROOT.** From `backend/`, three tests fail spuriously
   (`test_asgi.py::test_create_app_serves_real_components_route` and both `test_seed.py` CLI tests)
   because `scripts/seed_topology.py` resolves repo-root-relative. All three stories require test
   count accounting, so a spurious red would corrupt it.
6. **No live vendor data, unchanged.** Nothing in this sprint needs it; recorded so the absence is
   not mistaken for an oversight.

## Environment preconditions

- `uptime_dynamo_8021` container up; gate env `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`,
  `REQUIRE_DYNAMO=1`. A nonzero pytest SKIP count is an incomplete gate, not a pass.
- `frontend/node_modules` healthy at 216 top-level entries.
- Gate is **nine** commands. Baseline to compare against: **9/9 at `6d8847f`**, pytest 831 passed /
  0 skipped, npm 49 files / 334 tests.
- Scratch DynamoDB tables `rg147-*` and `rg155b-*` survive in the local container from sprint 73's
  reality gates. Harmless; they vanish when the container is recycled.

## Standing constraints carried into this sprint

- **Sprints 66–74 stay unmerged. Nothing touches `main`.** Acceptance at review is acceptance of the
  work, not authorisation to merge — ask the PO.
- **NEVER run `python -m src.composition.run`** — `decide` publishes recoveries with no human gate to
  the live public Statuspage.
- `.scrum/` is orchestrator-owned; subagents never write it, including via `git stash`.
- Briefs quote or cite `file:line`; never re-derive or paraphrase contract material.
- Console-script shims (`pytest.exe`, `lint-imports.exe`, `cfn-lint.exe`) blocked by Device Guard —
  module forms only.
- `plan-verification.md:19` forbids pre-declaring a story's wiki blast radius.
- Window check at every agent boundary (A21 hook): <85 dispatch freely · 85–94 finish the current
  story, start no new one · ≥95 park.

## Pre-lock verification — RAN, verdict **FIX-THEN-PROCEED**, all findings applied

**4 CRITICAL, 4 HIGH, 5 MEDIUM, 11 LOW.** Several probed by **execution**, not reading. The decision
to dispatch on an "internal" sprint was vindicated: **three of the four CRITICALs are gate-red at a
story's final commit**, and two are in the enforcement machinery — exactly where the dispatch reason
predicted they would be.

### The four CRITICALs

- **C1 — STORY-229 AC5 asserted the OPPOSITE of the truth for two of three branches.** It said
  *"option (c) moves the count; (a) and (b) do not."* Verification patched the tier to `reference`
  (option (b), nothing else changed) and ran the real tests: **two assertions failed** —
  `map_tier_count` 12 → 11 (`test_citation_gate.py:501`) and the BASELINE tier cross-check
  (`:325`, `:330-332`). Option (a) moves them too: the article yields **0** citations today because
  none carry a line number, so writing `file:line` per AC3 adds up to 58. AC5 rewritten to name all
  eight assertion sites plus the prose, unconditionally.
- **C2 — STORY-228 had NO citation-gate AC at all**, while its AC2 consolidates
  `zone-rules.md:57-100` — which is **inside the frontmatter comment block**, and
  `tools/citation_gate.py:75,82` scans frontmatter. `harness.py:62-69` occurs nowhere else in that
  article, so dropping it takes `total` 191 → 190 and reds two assertions. AC5 added. *(Moot for this
  sprint since 228 is held out, but fixed so it cannot resurface in sprint 75.)*
- **C3 — STORY-226 AC4 was unsatisfiable-or-theatre.** `service.py:22-29` is an unconditional
  passthrough and `FakeComponentRepository` never invokes `load_config`, so a component "whose config
  declared an empty description" cannot exist at that seam. Seeding `None` gives a test that passes
  identically before and after the fix; seeding an empty string can only be greened by normalizing
  downstream, which contradicts AC3 and the PO's ruling. AC4 replaced with a passthrough statement
  citing `service.py:28`.
- **C4 — STORY-229 AC2's stated verification mechanism is INERT.** It claimed the Facts lint and the
  citation gate would verify it *"not by reading"* — but both are green **right now**, on the article
  this story exists because it is wrong: `yt_wiki.py:262-263` *skips* unresolvable citations, the
  gate scores the article "vacuously clean", and **nothing in the repo checks that a `code_ref`
  exists on disk**. AC2 now requires a re-derived empty unresolvable list, and states that reading is
  the only mechanism that can see this.

### The HIGH that would have destroyed knowledge

**STORY-229 AC3 said "where a Fact cannot be checked, it is deleted, not carried."** Verification
classified all 36 unresolvable citations: **33 are merely MIS-ROOTED** (`api/client.ts` →
`frontend/src/api/client.ts` — the root cause STORY-223 documents) and **only 3 are genuinely gone**.
Deletion being the cheaper branch, a literal implementer would have destroyed 33 true Facts under an
AC written to protect knowledge. AC3 now requires re-rooting before judging anything uncheckable.

### Other applied fixes

- **HIGH 2** — wiki cost priced at zero on 226 and 227; both re-priced (see Scope).
- **HIGH 3** — 228's `Icon.tsx` edit would re-stale `frontend-zone.md` after 229 option (a), silently
  undoing this sprint's centrepiece. **The PO then chose exactly that branch at planning**, so the
  finding went live — resolved by running 228 FIRST (see Execution order), which removes the hazard
  by construction rather than by an instruction someone must remember.
- **HIGH 4** — 227 AC4's shown-RED was impossible: the test derives its expectation from the same
  constant it mutates, so it passes before *and* after. Corrected to the one mutation that works —
  empty `FIXTURE_PROPOSALS` to `[]`.
- **MEDIUM / LOW** — 228 named a nonexistent path (`frontend/src/nav/Icon.tsx` → the real
  `frontend/src/components/Icon/Icon.tsx`), plus the `Icon.test.tsx:21-40` array that would break
  `tsc -b`; 227 AC3 gained the `config-layer.md` re-key obligation **and** the probe result proving
  the NULL-vs-absent claim IS assertable (`'group' in item` discriminates, no low-level rewrite
  needed); 229's Facts measurement restated; 229's "Not in scope" narrowed because it contradicted
  AC1 option (c)'s `frontend/README.md` — the sprint-73 "three rules, no legal move" shape in
  miniature; 229 AC4's "verified by the link lint" replaced with a named grep, since the lint
  resolves archived targets and is green either way; 226 AC5's whitespace rule stated as code; 227
  AC5's "~6 lines" corrected to 26.

### What verification confirmed as sound

227 AC1 is feasible and strictly stronger than what it replaces — `app.openapi()` yields 11 paths and
**12** (method, path) pairs, with `/api/v1/maintenance` carrying both GET and POST, the case that
proves the pair table earns its keep — and it does not weaken STORY-155b's AC6. 226 AC1 is
satisfiable without the forbidden validator. The `tier: reference` constraints AC4 relies on are
genuinely enforced. Baseline preconditions reproduce exactly: **831 passed, 0 skipped**.
