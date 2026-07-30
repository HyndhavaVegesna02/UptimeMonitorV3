---
id: STORY-194
title: Zone-intent rule catalogue — write down the boundary rules the eight contracts cannot enforce
type: chore
points: 3
status: ready
refined: 2026-07-31   # refined and approved in-sprint-66 planning under the PO's standing
                      # autonomy directive (2026-07-31: "use your own reasoning, don't ask my inputs")
---

## Context

The PO asked for a sprint devoted purely to auditing boundary / code-discipline violations
(memory: `wanted-architecture-audit-sprint`, raised at sprint-65 planning and again at sprint-66
planning). The request came directly out of STORY-190: an inbound adapter persisting quarantine rows
through a core port **passes all eight `lint-imports` contracts** while being architecturally wrong.
If one such gap exists, others are probably already in the tree.

**An audit needs a yardstick before it starts, or it is opinion.** A planning probe (2026-07-31)
found the obvious violations absent — no `api → adapters` import, no outward import from `core`, no
inbound adapter holding a repository port — but found the *subtle* shape everywhere: vendor words
appear ~20 times inside `core/` (e.g. `core/domain/publication.py:4`,
`core/services/ingest_service.py:48`), all in explanatory prose. Whether that is compliant is a
judgement no document in this repo currently makes. Two auditors could read the same file and
disagree, and neither could be shown wrong.

This story writes the yardstick. STORY-195 and STORY-196 measure against it; STORY-197 mechanises
what can be mechanised.

## Description

Author `docs/scrum/wiki/zone-rules.md` — a living wiki article (so it goes stale by git arithmetic
like everything else) cataloguing the zone-intent rules that the eight existing contracts do **not**
enforce. Each rule is normative, sourced, cited both ways, and carries a coverage verdict.

The catalogue's body is the **gap**. Rules the gate already covers belong in a separate short
"already mechanical" section that names the contract — restating the gate as if it were the gap is
the failure mode to avoid.

Sources to mine, in priority order: `.scrum/working-agreements.md` (PO-stated rules outrank observed
patterns), the PO directive recorded in memory `code-boundary-discipline`, `CLAUDE.md` §"The four
backend zones", the dossier §4/§6 vocabulary rules in `uptime-monitor-v3-design.html`, and the eight
contracts in `pyproject.toml`'s `[tool.importlinter]` section.

Docs-only. No file under `backend/src/`, `frontend/` or `config/` changes.

## Acceptance Criteria

- [ ] **AC1** — `docs/scrum/wiki/zone-rules.md` exists as a conforming wiki article:
      `verified_sha` is a **short** sha (7–12 hex — the integrity check rejects a 40-char one) that is
      a real commit on `sprint-66`, and `code_refs` are **exactly the files the article's Facts cite**
      — not whole-zone directories. `python .claude/skills/yourteam/scripts/yt_wiki.py` reports
      **CLEAN** on the four blocking checks (`sweep`, `facts`, `links`, `integrity`) and adds **no new
      `refs` amplifier note**: `pyproject.toml` is already a `code_ref` in 5 articles against an
      `AMPLIFIER_THRESHOLD` of 4, so this article must **not** add it — the eight contracts are
      already owned by `architecture-boundary.md`, which this article links to instead of restating.
      (Verified at planning: `refs` is advisory unless `--strict-refs`, so it cannot fail the gate —
      but a catalogue that starts life by widening a known amplifier is the wrong first move.)
- [ ] **AC2** — Every rule is identified `ZR-n` and carries all four of: a one-sentence normative
      statement; its source (named file/section, PO directive with date, or working agreement);
      at least one **compliant** citation `file:line` from this repo; and a coverage verdict that is
      exactly one of `ENFORCED-BY <contract-name>` / `GUARDABLE (<how>)` / `UNGUARDABLE (<why>)`.
      A rule missing any of the four is not a rule yet.
- [ ] **AC3** — Every `path:line` citation in the article resolves at the recorded sha: the path
      exists and the file has at least that many lines. A citation-resolution sweep is run and its
      command plus output recorded in this story's History — not asserted from memory. (This is the
      mechanism that makes STORY-195/196 auditable; a catalogue citing a stale line teaches the
      auditors to distrust it.)
- [ ] **AC4** — The catalogue covers, at minimum, the five areas the PO named:
      (a) an adapter that persists — holding or calling a core/persistence port rather than
      returning values; (b) a core service reaching outward; (c) an `api` feature importing another
      feature or reaching an adapter directly; (d) vendor vocabulary escaping its adapter;
      (e) a constant duplicated across the `tools/` → `backend/src/` one-way boundary.
      Each is either a `ZR-n` rule in the body or an entry in the "already mechanical" section naming
      the contract that covers it — never silently absent.
- [ ] **AC5** — Rule (d) draws the line that today's repo cannot: an explanatory prose/docstring
      mention of a vendor is distinguished from a vendor word in an **identifier, type annotation,
      signature, or stored data value**, with one citation of each side from this repo. The existing
      `core/` docstring mentions are named as the **compliant** side, so STORY-195 cannot report
      ~20 false findings against them.
- [ ] **AC6** — Docs-only: `git diff --name-only` for this story's commit range shows no path under
      `backend/src/`, `frontend/` or `config/`. The five backend DoD commands exit 0 (pass/skip
      counts recorded; a nonzero skip count is an incomplete gate).

## Open Questions

None. Judgement calls (what counts as compliant vendor prose, which rules make the body vs the
"already mechanical" section) are the story's work, taken in-process under the PO's 2026-07-31
autonomy directive and reported at review.

## History

- 2026-07-31: drafted and refined in sprint-66 planning. 3 points: the reading is broad (four zones,
  two design documents, the working agreements) and the output is normative text that three later
  stories depend on being right.
- 2026-07-31: implemented. `docs/scrum/wiki/zone-rules.md` created (commit `b147676`), catalogued
  three GAP rules (`ZR-1` inbound-adapter-must-not-persist, `ZR-2` vendor vocabulary confined to
  its adapter, `ZR-3` `tools/`->`backend/src/` no-duplicate-constant) plus an "already mechanical"
  section naming `core-independence`, `api-feature-independence`, `api-outward-independence`,
  `adapters-edge-only` for areas (b)/(c) and the PO's "only composition sees both sides" rule,
  linking to `architecture-boundary.md` rather than restating the eight contracts (AC1, AC4).
  `verified_sha: 227d5bf` is the commit immediately preceding `b147676`; `git diff 227d5bf..HEAD --
  <code_refs>` is empty (verified).
  AC3 citation-resolution sweep (ad hoc script, 8 citations checked against the article's file:line
  claims): all 8 `OK` (path exists, line index within file length, and line content matches the
  cited symbol/text), 0 failures. Command: a fixed-manifest Python script reading each
  `(path, line, expected_substring)` triple from the article and asserting
  `path.exists()` and `len(lines) >= line` and `expected_substring in lines[line-1]`; ran from repo
  root at commit `b147676`. Sample output:
  ```
  OK backend/src/adapters/inbound/dynatrace/adapter.py:26 -- 'def fetch_observations('
  OK backend/src/core/services/ingest_service.py:121 -- 'self._rejected_repo.save('
  OK backend/src/core/domain/signal.py:6 -- 'heard of Dynatrace (vocabulary rule P3, dossier §6).'
  OK backend/src/core/ports/status_publisher.py:14 -- 'class StatusPublisherPort(ABC):'
  OK backend/src/core/ports/status_publisher.py:18 -- 'def publish(self, change: StatusChange) -> None:'
  OK backend/src/adapters/outbound/statuspage/__init__.py:23 -- 'class StatuspagePublisher(StatusPublisherPort):'
  OK backend/src/adapters/inbound/dynatrace/health_mapping.py:35 -- 'PROVISIONAL_STATUS_MAPPING: dict[tuple[str, str], Health] = {'
  OK tools/demo_engine/assumed_failure_codes.py:31 -- 'from src.adapters.inbound.dynatrace.health_mapping import PROVISIONAL_STATUS_MAPPING'
  Checked 8 citations, 0 failure(s).
  ```
  `python .claude/skills/yourteam/scripts/yt_wiki.py` (run at HEAD `b147676`): `sweep: CLEAN`,
  `facts: CLEAN`, `links: CLEAN`, `integrity: CLEAN`; `refs: 2 note(s)` (pre-existing amplifier
  notes for `backend/src/composition/run.py` and `pyproject.toml` — neither is a `code_ref` of
  `zone-rules.md`, so this article adds no new amplifier note, per AC1).
  AC5: rule `ZR-2` names `core/domain/signal.py:6` as the compliant (prose) side and
  `adapters/outbound/statuspage/__init__.py:23` (`StatuspagePublisher`) as the illustrative
  forbidden-form side, verified by an AST walk of every `core/` module's function/class/arg/Name
  nodes for vendor substrings returning zero hits (only grep hits inside docstring/comment text),
  so STORY-195 cannot report the ~20 `core/` prose mentions as findings.
  AC6: `git diff --name-only 227d5bf..HEAD` (this story's only commit, `b147676`) touches exactly
  one path, `docs/scrum/wiki/zone-rules.md` — nothing under `backend/src/`, `frontend/`, or
  `config/`.

- 2026-07-31: FIX ROUND (spec verdict FAIL on AC5, quality verdict FIX_REQUIRED: 5 MAJOR, 9 minor).
  Commits: `c0a4d71` (the rewrite) and `8e63aad` (re-stamp `verified_sha` to `c0a4d71`).
  **F1/AC5 (ZR-2 rewritten FORM-based).** Statement now keys on three CLOSED compliant forms
  (`#` comment; formal docstring; the bare-string "attribute docstring" idiom, exemplar
  `backend/src/core/domain/publication.py:66`) vs. a closed forbidden-form set (identifier,
  annotation, signature, dict key, stored value), with the vendor-word list explicitly demoted to a
  labelled non-exhaustive GUARD detection seed, never the rule's definition. Added the Provenance
  carve-out (dossier P3, `uptime-monitor-v3-design.html:422`; `backend/src/core/domain/signal.py:26-39`)
  since a blanket stored-value ban would have contradicted the domain's own sanctioned vendor-id
  channel. Settled the six previously-unadjudicated citations
  (`backend/src/core/domain/component.py:17`, `backend/src/core/domain/publication.py:35`,
  `backend/src/core/ports/component_repository.py:53`,
  `backend/src/core/ports/observation_repository.py:5` and `:7`,
  `backend/src/core/ports/__init__.py:7`) as COMPLIANT prose under the new rule — verified by
  re-reading each line directly.
  **F2 (ZR-1 contract sketch narrowed).** `forbidden_modules` now enumerates the 9 persistence/
  repository port modules by name, excluding `backend/src/core/ports/signal_ingest.py:3-8` (the core's
  front door, which dossier §6/§8 lets a driving/push adapter legitimately reference) and
  `clock`/`status_publisher` (not persistence). A maintenance-note comment sits next to the sketch.
  **F3 (ZR-2 guard sketch coverage stated honestly).** Extended to name `ast.Attribute.attr`,
  `ast.keyword.arg`, and `ast.Constant` (excluding bare-`Expr` docstring/attribute-docstring
  constants) alongside the original `FunctionDef`/`ClassDef`/`arg`/`Name` walk, and now states the
  residue in the article text (string annotations, dynamically constructed identifiers) rather than
  claiming "the exact discrimination this rule needs."
  **F4 (ZR-3 pinned).** Scope pinned to module-level UPPER_CASE constant declarations (not every
  `ast.Constant`); the "no import edge" exemption replaced with "unless the `tools/`-side symbol is
  imported from `src` at runtime"; a real, adjudicated violation added
  (`tools/demo_loop_gate/harness.py:746-750` hardcodes `"uptime-observations"`/`"uptime-control"`,
  already declared at `backend/src/composition/settings.py:21-22`, despite `harness.py:61` already
  importing a sibling `src.composition.config` symbol — proving the dropped exemption would have
  falsely cleared it). **Re-measured independently rather than trusted from the hand-off:** wide
  reading (every scalar `ast.Constant` value under `tools/` vs `backend/src/`) = 101 distinct
  colliding values (not 105 as quoted at hand-off — flagged as a factual discrepancy, not silently
  substituted; the qualitative conclusion is unaffected either way); narrow reading (module-level
  UPPER_CASE constants only) = 0 colliding values by literal-equality (the `assumed_failure_codes.py`
  compliant pair agrees via IMPORT, invisible to a literal-value test; the `harness.py` violation is
  exactly what the pinned scope + import-exception is FOR). Command used: an ad hoc AST script
  comparing distinct scalar-constant sets under each tree (recorded below in the citation-sweep
  section's sibling script, `zr3_measure.py`/`zr3_measure2.py`/`zr3_measure3.py`, run from the repo
  root at HEAD).
  **F5 (two new rules added).** `ZR-4` (five-file `api/v1` convention): checked all ten features
  (`ls backend/src/api/v1/*/`) — nine are exactly five files; `health`
  (`backend/src/api/v1/health/controller.py`, 2 files) is the one documented exception (its own
  docstring: a liveness stub kept only to make `api-feature-independence` non-vacuous). `ZR-5`
  (composition-root `CONFIG_DIR` parity): **honest finding — no current code-level divergence
  exists.** `backend/src/composition/run.py:182-184` and `backend/src/composition/app.py:97,137`
  both route through the identical `composition/settings.py::load_settings().config_dir`; the
  sprint-64 incident's actual failure mode is OPERATIONAL (two separate OS processes each reading
  their own env), which no single-process test or import-linter contract can see. Flagged explicitly
  to the coordinator rather than fabricating a violating citation neither side of this rule has today.
  **F6 (nine minors).** All applied: STORY-190 counterfactual moved to the Inference section; ZR-3
  given ONE operative `GUARDABLE` verdict (the lint-imports inapplicability folded into its text,
  not stated as a second verdict); vendor-vocabulary source attribution split correctly across PO
  concrete rule 1 (`code-boundary-discipline.md:28-29`, "vendor vocabulary never leaves it") and rule
  3 (`code-boundary-discipline.md:31-32`, port domain-typing); the "only composition sees both sides"
  claim given a precision parenthetical (`adapters/inbound/dynatrace/adapter.py` already imports both
  `src.core.domain` and a sibling `src.adapters.inbound.dynatrace` module, which is ordinary
  within-package organization, not composition's cross-zone privilege); ZR-2's stated scope widened
  to `domain`/`ports`/`services`/`queries`/package-root to match what its guard (and this story's AST
  verification) already covers; ZR-1's coverage verdict now names the RED-proving mutation for
  STORY-197 (temporarily import a repository port into `adapter.py`, even unused, then revert); the
  zone-wide-negative caveat added (ZR-1's "0 violations" and ZR-2's "zero core identifiers" are
  verified over whole zones, not this article's narrow `code_refs` — falsification elsewhere would
  not trip the sweep; mitigation is the inline re-derivation commands plus STORY-197 AC6's mandatory
  re-adjudication before any `verified_sha` re-stamp); the `signal.py` citation fixed to `:5-6`.

  **Factual disagreements flagged (per instruction, not silently substituted):** (1) the 105-vs-101
  constant-collision count above; (2) `backend/tests/test_zone_layout.py`'s
  `test_zone_layout_agreements` function actually spans lines 125-173, not 125-174 as quoted at
  hand-off (the file has exactly 173 lines) — the citation-sweep script caught this directly and it
  is fixed in the article; (3) ZR-5 has no current violating citation to give — both composition
  roots agree today; a fabricated one was not written in its place.

  **AC3 sweep rebuilt to EXTRACT citations from the article** (fix-round re-verification requirement
  1), replacing the original hand-typed manifest. Regex:
  `` `([\w./\\-]+\.(?:py|md)):((?:\d+(?:-\d+)?)(?:,\d+(?:-\d+)?)*)` `` over the whole article text,
  resolving each `(path, line-spec)` against the repo (one citation, `code-boundary-discipline.md`,
  resolves against the Claude memory directory instead, since it is a memory file, not a repo file).
  Command: `python citation_sweep_v2.py` (scratchpad script), run at HEAD `8e63aad`. Full output:
  ```
  OK   memory/code-boundary-discipline.md:28-29 (file has 36 lines)
  OK   backend/src/adapters/inbound/dynatrace/adapter.py:26 (file has 43 lines)
  OK   backend/src/core/services/ingest_service.py:121 (file has 144 lines)
  OK   backend/src/core/ports/signal_ingest.py:3-8 (file has 27 lines)
  OK   backend/src/core/domain/publication.py:66 (file has 80 lines)
  OK   backend/src/core/domain/signal.py:26-39 (file has 92 lines)
  OK   backend/src/core/domain/signal.py:27 (file has 92 lines)
  OK   backend/src/adapters/inbound/dynatrace/_assembly.py:110 (file has 118 lines)
  OK   memory/code-boundary-discipline.md:31-32 (file has 36 lines)
  OK   backend/src/core/domain/signal.py:5-6 (file has 92 lines)
  OK   backend/src/core/ports/status_publisher.py:14-19 (file has 20 lines)
  OK   backend/src/core/domain/component.py:17 (file has 33 lines)
  OK   backend/src/core/domain/publication.py:35 (file has 80 lines)
  OK   backend/src/core/ports/component_repository.py:53 (file has 56 lines)
  OK   backend/src/core/ports/observation_repository.py:5 (file has 49 lines)
  OK   backend/src/core/ports/observation_repository.py:7 (file has 49 lines)
  OK   backend/src/adapters/persistence/dynamo_observation_repository.py:58-62 (file has 151 lines)
  OK   backend/src/core/ports/__init__.py:7 (file has 40 lines)
  OK   backend/src/adapters/outbound/statuspage/__init__.py:23 (file has 56 lines)
  OK   tools/demo_engine/assumed_failure_codes.py:31 (file has 71 lines)
  OK   backend/src/adapters/inbound/dynatrace/health_mapping.py:35 (file has 88 lines)
  OK   tools/demo_loop_gate/harness.py:746-750 (file has 971 lines)
  OK   backend/src/composition/settings.py:21-22 (file has 119 lines)
  OK   tools/demo_loop_gate/harness.py:61 (file has 971 lines)
  OK   backend/src/api/v1/decisions/__init__.py:6 (file has 6 lines)
  OK   backend/tests/test_zone_layout.py:125-173 (file has 173 lines)
  OK   backend/src/composition/run.py:182-184 (file has 223 lines)
  OK   backend/src/composition/app.py:97,137 (file has 228 lines)
  OK   tools/demo_loop_gate/harness.py:519 (file has 971 lines)
  OK   tools/demo_loop_gate/harness.py:580 (file has 971 lines)

  Extracted 35 citation occurrence(s), 30 distinct (path, line-spec) pair(s) checked, 0 failure(s).
  ```

  **code_refs widened** (F1/F4/F5 introduce new citations) to: `backend/src/core/domain/publication.py`,
  `backend/src/core/domain/component.py`, `backend/src/core/ports/component_repository.py`,
  `backend/src/core/ports/observation_repository.py`, `backend/src/core/ports/__init__.py`,
  `backend/src/core/ports/signal_ingest.py`, `tools/demo_loop_gate/harness.py`,
  `backend/src/composition/settings.py`, `backend/src/composition/run.py`,
  `backend/src/composition/app.py`, `backend/tests/test_zone_layout.py`,
  `backend/src/api/v1/health/controller.py`, `backend/src/api/v1/decisions/__init__.py`,
  `backend/src/adapters/persistence/dynamo_observation_repository.py` — still NOT `pyproject.toml`.
  `verified_sha` re-stamped to `c0a4d71` (the rewrite's own commit); `git diff c0a4d71..HEAD --
  <all 21 code_refs>` is empty (verified — the only later commit only edits the frontmatter sha
  string).

  `python .claude/skills/yourteam/scripts/yt_wiki.py` at HEAD `8e63aad`: `sweep: CLEAN`,
  `facts: CLEAN`, `links: CLEAN`, `integrity: CLEAN`. `refs: 2 note(s)`:
  `pyproject.toml` unchanged (5 articles, not a `code_ref` of `zone-rules.md`, per AC1);
  `backend/src/composition/run.py` moved from 4 to 5 articles — a REAL widening this rewrite
  introduces (ZR-5 genuinely needs to cite `run.py`'s own config-resolution code), flagged here
  rather than silently absorbed; `refs` stays advisory and does not block either check.

  **Full backend DoD gate re-run** (`REQUIRE_DYNAMO=1 DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`,
  all five commands, at HEAD `8e63aad`): `pytest` 685 passed, 0 skipped; import-boundary 8 kept / 0
  broken; `ruff check .` clean; `ruff format --check .` 242 files already formatted; `cfn-lint
  infra/stack.yaml` clean (empty output, exit 0).

  AC6 re-confirmed: `git diff --name-only d4ad03e..HEAD` touches only `.scrum/sprint-current.yaml`,
  `docs/scrum/sprints/2026-07-31-sprint-66/plan.md`, `docs/scrum/stories/STORY-194-*.md`,
  `docs/scrum/wiki/zone-rules.md` — nothing under `backend/src/`, `frontend/`, or `config/`.
