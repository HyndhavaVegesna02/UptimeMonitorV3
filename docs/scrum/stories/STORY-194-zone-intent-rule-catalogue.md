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
