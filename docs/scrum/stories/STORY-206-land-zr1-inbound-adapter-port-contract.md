---
id: STORY-206
title: Land ZR-1's guard — an import-linter contract forbidding inbound adapters from importing repository ports
type: chore
points: 3
status: draft
filed: 2026-07-31
refined: 2026-08-05
sprint: 69
---

> **REFINED at sprint-69 planning (2026-08-05), then CORRECTED at plan verification.** The AC are
> lifted from `docs/scrum/wiki/zone-rules.md` ZR-1's Coverage verdict and re-verified against HEAD;
> they are a PROPOSAL until the PO approves the sprint. **Estimate 2 → 3**, but not for the reason
> the first pass gave — the completeness test moved to STORY-220 and the doc ripple turned out to be
> nine living files, not three. See "The doc ripple" and "Why 3, and what moved out".

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
`docs/scrum/wiki/zone-rules.md` ZR-1 (`:87-139`) — the Coverage verdict holds the contract
VERBATIM; lift it rather than re-deriving it.

An inbound adapter is a pure translation function: it returns canonical values and persists
nothing. Persistence is core's job, done by the service the adapter's return value is handed to
(`backend/src/core/services/ingest_service.py:121` calls `self._rejected_repo.save(...)`, not the
adapter). Nothing violates this today — which is why the guard must be proven by mutation.

## Re-verification at HEAD (2026-08-05, planning)

- The nine enumerated port modules all exist under `backend/src/core/ports/`:
  `component_repository`, `maintenance_repository`, `observation_repository`, `proposal_repository`,
  `publication_repository`, `rejected_observation_repository`, `sample_mode_repository`,
  `signal_repository`, `watermark`. The three deliberately excluded modules also exist and are
  correctly excluded: `signal_ingest` (the core's documented front door, dossier §6/§8),
  `clock`, `status_publisher` (neither is persistence).
- `grep -rn "from src.core" backend/src/adapters/inbound/` returns **five** hits, all
  `from src.core.domain import ...` — **zero** `src.core.ports` imports. The tree is clean, so
  AC3's mutation is the only possible red.
- `pyproject.toml` declares **eight** contracts today
  (`grep -c "\[\[tool.importlinter.contracts\]\]"` = 8). This story makes it nine.
- **The contract loads and trips — verified, not assumed.** Plan verification ran the real
  `importlinter` CLI against a scratch TOML holding this contract verbatim:
  `inbound-adapters-dont-persist KEPT`, exit 0, 151 files / 432 dependencies. It then rebuilt the
  grimp graph, added the AC3 edge in memory and re-ran `ForbiddenContract.check` → `kept=False`.
  `source_modules = ["src.adapters.inbound"]` matches the package-level shape the existing eight
  contracts use.

## The doc ripple is nine living files, not three — corrected at plan verification

The first refinement pass claimed the count of record "eight" lived in three places. **That was
wrong**, and the repo had already measured it: `.scrum/sprint-current.yaml:204-206` and sprint 68's
plan recorded *"15 occurrences of 'eight contracts' across 6 LIVING files"*. Plan verification
re-swept and found contract-count claims in **nine** living files — beyond the three originally
named, also `.scrum/definition-of-done.md:50/51/56` (which **also lists all eight contracts by name
at `:52-54`**), `docs/scrum/wiki/zone-rules.md:2` (the frontmatter title) `:17/26/69/85/516/519/622/736/739/781`,
`docs/scrum/wiki/dev-setup-and-dod.md:81/85/310`, `docs/scrum/wiki/ingest-service-and-pull-loop.md:11/96`,
`docs/scrum/wiki/config-layer.md:274`, `docs/scrum/wiki/api-five-file-convention.md:21`.

**And a naive sweep breaks correct text.** The same files carry `eight`/`8` for the **DoD command
count**, which must NOT change: `CLAUDE.md:188` ("8 commands"),
`docs/scrum/wiki/dev-setup-and-dod.md:118` ("Eight commands in total"), and — inside the
adjudication legend itself — `docs/scrum/wiki/zone-rules.md:802` ("runs inside the existing eight
DoD commands"). AC4 is written as a discrimination rule for exactly this reason.

Also noted: `pyproject.toml` is a `code_ref` in **five** wiki articles, so the DoD forward
blast-radius check will flag all five. That is expected, not a surprise to discover at gate time.

## Why 3, and what moved out

The audit's first cut was 2 — contract plus a three-site doc edit. The contract is small; the
**~20-site sweep with a discrimination rule** is the work, and it is why this is a 3.

A completeness test (originally AC6 here — assert the contract's `forbidden_modules` equals the
persistence ports on disk, so ZR-1's prose *"a newly added port MUST be appended in the SAME
commit"* stops being a promise) **has been split out as STORY-220**, proposed for sprint 70. It is
right, and it is not dropped — but carrying it here makes this a 5 and the sprint a 13, against a
PO pacing directive to sit near 9–11. Until it lands, ZR-1's guard is complete only as far as a
human maintains the list, and the row must not claim otherwise.

## Acceptance Criteria

- [ ] **AC1 — the contract exists, verbatim from the catalogue.** `pyproject.toml` gains a ninth
      `[[tool.importlinter.contracts]]` entry: `name = "inbound-adapters-dont-persist"`,
      `type = "forbidden"`, `source_modules = ["src.adapters.inbound"]`, and `forbidden_modules`
      enumerating exactly the nine port modules listed in ZR-1's Coverage verdict — no more, no
      fewer. The maintenance-note comment ships with it.
- [ ] **AC2 — the three exclusions are deliberate and recorded.** `src.core.ports.signal_ingest`,
      `src.core.ports.clock` and `src.core.ports.status_publisher` are absent from
      `forbidden_modules`, and the comment states why (front door per dossier §6/§8; the other two
      are not persistence). A whole-package ban would forbid a shape the design documents — the
      commit message says so.
- [ ] **AC3 — shown RED by mutation (A9).** Temporarily add
      `from src.core.ports.observation_repository import ObservationRepository` to
      `backend/src/adapters/inbound/dynatrace/adapter.py` — an unused annotation is enough, it need
      never be called. The import-boundary DoD command exits **nonzero** and its output **names
      `inbound-adapters-dont-persist`**. Revert; the same command exits 0; `git diff` is empty.
      Both invocations and their output tails are recorded verbatim in the board's `reality_gate`
      block. A guard that has only ever been green is not accepted.
- [ ] **AC4 — the count of record moves 8 → 9 in the SAME commit as AC1, by a stated
      discrimination rule.** The rule, not a site list: **a claim about the number of import-linter
      CONTRACTS changes; a claim about the number of DoD COMMANDS does not.** The sweep covers
      LIVING files only — `CLAUDE.md`, `.scrum/`, `docs/scrum/wiki/` — and explicitly excludes
      `docs/scrum/sprints/` and `docs/scrum/stories/`, which are append-only history (the STORY-210
      AC2 pattern). Where a file lists the contracts BY NAME
      (`docs/scrum/wiki/architecture-boundary.md:22`, `.scrum/definition-of-done.md:52-54`), the
      ninth is added to the list. Evidence: before/after of
      `grep -rniE "eight|\b8\b" CLAUDE.md .scrum/ docs/scrum/wiki/`, recorded in the commit, with
      every surviving occurrence individually classified as a command-count claim (unchanged, by
      design) or unrelated. **Zero surviving contract-count claims of "eight" is the criterion —
      not zero occurrences of the word.**
- [ ] **AC5 — no ninth DoD command.** The contract lands inside the EXISTING import-boundary
      command (`python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`).
      The DoD stays at eight commands; `.scrum/definition-of-done.md`'s command list does not grow.
      The three sites named in AC4 as command-count claims are the proof this distinction was held.
- [ ] **AC6 — the catalogue row flips honestly, in a shape STORY-216 can parse.**
      `docs/scrum/wiki/zone-rules.md`'s adjudication table changes ZR-1 from
      `GUARDABLE-DEFERRED (STORY-206)` to `ENFORCED-BY` naming the contract
      `` `inbound-adapters-dont-persist` `` as a backtick code span in the **Verdict** cell — an
      import-linter contract name is a first-class guard reference, and STORY-216 AC1 resolves it
      against `pyproject.toml` (coordinated: that AC was widened at plan verification for this row).
      The Detail column records the AC3 mutation (what was added, where, what tripped) — because
      the table's own legend defines `ENFORCED-BY` as requiring a guard shown RED, never merely "is
      green" — **and states that the forbidden-module list's completeness is maintained by hand
      until STORY-220 lands.** `verified_sha` bumped in the same commit as the code it describes
      (A18 / C3).
- [ ] **AC7 — the five articles citing `pyproject.toml` are handled, not discovered at the gate.**
      `pyproject.toml` is a `code_ref` in `architecture-boundary`, `api-five-file-convention`,
      `config-layer`, `dev-setup-and-dod` and `sample-mode`. Each is updated or explicitly
      re-verified (`verified_sha` bumped) before this story passes its DoD forward blast-radius
      check.

## Not in scope

ZR-2's AST walk (STORY-207). The forbidden-list completeness test (**STORY-220**, split out at plan
verification). Any change to what the inbound adapter returns. Widening the contract to
`src.core.ports` as a package — explicitly rejected above, with the reason.
