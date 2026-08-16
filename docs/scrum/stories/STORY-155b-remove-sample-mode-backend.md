---
id: STORY-155b
title: Remove sample_mode from the backend, and tombstone its article
type: chore
points: 7          # RE-PRICED 5 -> 7 at pre-lock verification, 2026-08-15. See "Why 7, not 5".
status: ready
refined: 2026-08-15   # sprint-73 planning; split from STORY-155 (an 8). PENDING PO lock.
sprint: null
---

## Depends on STORY-155a

**155a removes the consumer; this removes the producer.** 155a must be `done` before this starts.

> ⚠ **The ordering reason stated at planning was WRONG and is corrected here.** I claimed removing
> the backend first would leave the SPA "calling a 404" in a broken state. Verification refuted it:
> the SPA **degrades gracefully** — `client.ts:73-79` throws `ApiError(status=404)`,
> `TopBar.tsx:52-58` renders *"Sample mode unavailable — retry"* instead of the switch, and
> `TopBar.test.tsx:126` already covers exactly that path. **The order still stands, but for a
> different reason:** 155a's diff stales `sample-mode.md` (nine of its `code_refs` are files 155a
> touches), and this story archives that article. Consumer-first archives it **once** instead of
> updating-then-archiving.

## Context

`sample_mode` is the on-demand outage simulator (STORY-048), **TEMPORARY by PO directive
2026-07-03**, superseded by the Grail demo engine. `CLAUDE.md` names STORY-155 as its removal.

### ⚠ "Inert" means the flag is off — NOT that the code is unwired

**`SampleModeIngest` is live in the pull loop.** `composition/run.py:101` wraps the real
`IngestService`; `composition/app.py:47` takes the param, `:129` constructs a real
`DynamoSampleModeRepository` when it is `None`, and `:213` assigns `app.state.sample_mode_repo`.
It is a **decorator over the ingest front door**, so removal changes the wiring of the live ingest
path — behaviour-preserving only because the flag reads false.

**Verification added one thing planning missed:** `composition/sample_mode.py:61` performs a
control-table `is_enabled()` read **once per ingest cycle**. Removal therefore also deletes a
per-cycle DynamoDB call. AC1's comparison is pinned at the **observation** level for exactly this
reason — a DB-call-count comparison would legitimately differ and prove nothing.

## Why 7, not 5

Re-priced at pre-lock verification. The 5 counted the code and **priced the wiki at zero** — while
this same sprint bumped STORY-147 from 2 to 3 *because* its diff reaches five `verified`/`tier: map`
articles that A18 forces re-verified in-story. That rule was applied to the small story and withheld
from the big one.

**This story's diff overlaps NINE `tier: map` / `status: verified` articles**, every one of which
`.scrum/definition-of-done.md:133-136` requires updated or explicitly re-verified **within the
story**: `api-five-file-convention.md`, `architecture-boundary.md`, `canonical-types-and-ports.md`,
`config-layer.md`, `ingest-service-and-pull-loop.md`, `persistence-adapters.md`,
`statuspage-publish.md`, `zone-rules.md`, and `sample-mode.md` itself. `pyproject.toml` alone is a
`code_ref` in four of them — at or above `yt_wiki.py`'s `AMPLIFIER_THRESHOLD = 4`.

Several carry **live present-tense claims** that AC7's catch-all covers only in spirit:
`api-five-file-convention.md:33,45,60` · `persistence-adapters.md:32,39` · `zone-rules.md:154,488` ·
`ingest-service-and-pull-loop.md:212-214` (which still says `PostgresSampleModeRepository`).

**The wiki work cannot be split out into a follow-up story.** A18 makes it in-story by rule.

## The removal recipe: a genuine asset that you may not follow blind

`docs/scrum/wiki/sample-mode.md:226` holds a mechanical deletion checklist (STORY-048 AC7c).
Verification checked it line by line. **Correct:** all four test-file deletions,
`core/ports/__init__.py`, `tests/fakes.py`, `api/dependencies.py:13-14,58-61`,
`api/v1/__init__.py:13,26`, `run.py`, `test_run_live_loop.py`, and the "all five files" claim.

**Wrong — do not follow these:**

| Recipe says | Reality |
| --- | --- |
| `adapters/persistence/sample_mode_repository.py` | `dynamo_sample_mode_repository.py` |
| app.py's "`PostgresSampleModeRepository` import" | it is `DynamoSampleModeRepository` (`app.py:87-88`) — Postgres is the superseded stack |
| pyproject: remove from `api-feature-independence` | **names 1 of 3 contracts** — see AC2 |
| `:311` "the control table under the `SAMPLE_MODE` **partition**" | it is the **sort key**: `pk="CONFIG"`, `sk="SAMPLE_MODE"` (`dynamo_sample_mode_repository.py:18-19`). **A delete keyed on the partition is a no-op.** |

### A landing pad already exists

`backend/tests/test_zr1_forbidden_list_completeness.py:35` and `:195-196` name this story and
pre-record that the count goes to **8** — the same courtesy STORY-179 left STORY-173.

## Acceptance Criteria

- [x] **AC1 (the live ingest path is provably unchanged) — the AC that justifies the estimate.**
      Prove the pull loop records the **same observations** with `SampleModeIngest` removed.
      **Use `run_periodic`, not `build_live_loop`:** `test_run_live_loop.py:94` patches `run_periodic`
      outright and records zero observations — it asserts `isinstance(ingest_port, SampleModeIngest)`
      at `:130`, which after removal becomes a one-word `IngestService` edit that proves nothing.
      That is the theatre this AC exists to prevent and it is the path of least resistance.
      The harness that works: `test_pull_loop.py:349, :435, :754-757` drives `run_periodic` with a
      real `IngestService` and `FakeObservationRepository`.
      **The "before" arm cannot live in the suite**, because AC2 deletes the before-object in the
      same story. Capture the pre-removal observations as **recorded evidence** and compare against
      the post-removal run. Compare at the **observation level**, never DB-call counts
      (`sample_mode.py:61`'s per-cycle read legitimately disappears).
      ⚠ `test_sample_mode_end_to_end.py:116` is the existing behavioural proof that flag-OFF is
      byte-identical passthrough — **read it before deleting it**; it is the shape AC1 wants.
- [x] **AC2 (`pyproject.toml`'s THREE import-linter contracts) — a gate break if missed.**
      `pyproject.toml:79` (`api-feature-independence`), `:105` (`api-shared-no-feature-imports`),
      `:141` (`inbound-adapters-dont-persist`) all name sample-mode modules. Verified by probe:
      an **independence** contract naming a deleted module fails with `Module 'X' does not exist.`
      (**exit 1**); a **forbidden** contract naming one passes **silently at exit 0**. So `:79`
      reds DoD command 2, and `:105` would **rot invisibly forever**. Remove all three.
- [x] **AC3 (the ZR1 guard moves deliberately, via the right assertion)** —
      `test_zr1_forbidden_list_completeness.py` is updated in the same commit as the deletion, its
      count reaching the **8** the file already predicts. **The shown-RED must come from the
      set-equality test at `:216-236` (`declared == discovered`), NOT the floor** — the floor is
      `>= 5` deliberately and will not go red on this removal. Mutating the floor proves nothing.
- [x] **AC4 (`test_citation_gate.py` moves with the archive)** —
      `backend/tests/test_citation_gate.py:242-251` asserts `found == set(BASELINE)` where `found`
      is the literal glob `docs/scrum/wiki/*.md`. `BASELINE` carries a `"sample-mode.md"` key at
      `:212`. AC8 moves the article out of that glob, so **the key must be removed in the same
      commit** or pytest reds at this story's last commit.
- [x] **AC5 (no `sample_mode` remains in backend source or tests)** —
      `grep -ri "sample_mode" backend/ --exclude-dir=__pycache__ --exclude-dir=*.egg-info` returns
      **zero**. ⚠ The `egg-info` exclusion is required, not cosmetic:
      `backend/uptime_monitor_v3.egg-info/SOURCES.txt` matches, so without it **this AC can never be
      satisfied**. The `SampleModeRepository` port and its `__all__` entry are gone from
      `core/ports/__init__.py`.
- [x] **AC6 (the API surface loses the route cleanly)** — `GET`/`PUT /api/v1/sample-mode` no longer
      exists, the registration is gone from `api/v1/__init__.py`, and **no other route changed** —
      asserted against the remaining route table.
- [x] **AC7 (the DynamoDB row is deleted with the CORRECT key)** — the flag is
      `pk="CONFIG"`, `sk="SAMPLE_MODE"` (`dynamo_sample_mode_repository.py:18-19`) — **not a
      `SAMPLE_MODE` partition, which is what the recipe says and what would make the delete a
      no-op.** Delete it with a documented one-liner, or record explicitly why a stale row in a dev
      table is harmless. Do not leave it unmentioned.
- [x] **AC8 (the article is TOMBSTONED, with the keys the lint enforces)** — `sample-mode.md` moves
      to `docs/scrum/wiki/archive/` as `tier: reference`, dropping `code_refs` and Facts, and
      **carrying `archived_sprint` and `archived_reason`** — `yt_wiki.py:388-397` enforces both on
      every file under `archive/`. The reason states *why* the feature died (superseded by the demo
      engine; PO directive 2026-07-03) — the protocol's rule that deletion adds knowledge. Every
      internal link to it is repointed or pruned, verified by the link lint.
- [x] **AC9 (the NINE overlapping articles are each updated or re-verified IN-STORY)** — per
      `.scrum/definition-of-done.md:133-136`. The live present-tense claims listed above are the
      known ones; the post-commit sweep decides the rest. **This is the scope that re-priced the
      story and it is not optional.**
- [x] **AC10 (`tools/` is not left broken — it is outside every gate command)** —
      `tools/demo_loop_gate/harness.py:800-803` asserts `GET /sample-mode == {"enabled": False}` as
      its own AC1(c); after this story that is a 404. **No DoD command runs it**, so nothing would
      catch the break — and the demo-loop gate is the project's only proven end-to-end verification
      since the vendor trial expired. Update it and state that you ran it.
- [x] **AC11 (gate, and the count is explained)** — full 9-command gate exits 0 at the final HEAD.
      Four dedicated test files are deleted, so the backend count **will drop**: state before/after
      and account for the delta exactly.

## Not in scope

Frontend removal (STORY-155a, which lands first). `tools/ui-sweep/sweep.mjs:194-231` — that drives
the frontend trigger and belongs to 155a. Repairing mojibake in other articles (STORY-192 — archiving
this article removes ~110–142 of its sequences; **re-measure 192 afterwards**).

## Open Questions

None.

## History

- 2026-08-16: **AC7 (the DynamoDB row).** Checked the CORRECT key
  (`pk="CONFIG", sk="SAMPLE_MODE"` — the sort key, per the recipe correction above,
  not the `SAMPLE_MODE` partition the old recipe named) against every control table
  visible on the local DynamoDB Local instance used for dev/CI
  (`uptime-control`, plus leftover scratch tables `custom-control-table`,
  `rg147-ctrl` from earlier stories' reality-gate runs): `get_item` returned no
  `Item` on any of them — the flag was never set on this machine. There is
  therefore no row to delete here. The documented one-liner, for any table that
  DOES carry a stale row (e.g. a developer machine that ran sample-mode live
  before this story):
  `table.delete_item(Key={"pk": "CONFIG", "sk": "SAMPLE_MODE"})` against the
  `dynamo_control_table` resource. A stale row left behind on such a machine is
  harmless either way: `DynamoSampleModeRepository` (this story's AC2) no longer
  exists, so nothing in the codebase reads or writes that key any more — it
  would sit as one inert, unreferenced item, not a security or correctness
  hazard. Production has no live table at all (`CLAUDE.md`'s "Deployed
  topology" section — the AWS stack was decommissioned 2026-08-13), so there is
  no live-table case to address.
- 2026-08-16: **Why sample_mode was removed** (feeds AC8's wiki tombstone
  reason): `sample_mode` was the on-demand outage simulator (STORY-048),
  declared TEMPORARY by PO directive 2026-07-03, and was superseded by the
  Grail demo engine (`tools/demo_engine/`), which reached the same
  demonstration goal — exercising the real degrade→approve→publish→recover
  loop — without a bespoke, always-armed decorator sitting over the live
  ingest front door. STORY-155a removed the frontend consumer first
  (2026-08-15/16); this story removes the backend producer and archives its
  wiki article, closing the feature out per `CLAUDE.md`'s standing note that
  STORY-155 is its removal.
- 2026-08-16: **AC11 (the count, before/after, accounted exactly).** Backend
  `pytest`: **before 851 passed / 0 skipped** (the sprint baseline recorded at
  STORY-155a's `f6ce2c6`), **after 831 passed / 0 skipped** — net **−20**.
  Accounted exactly, not merely reconciled to the right total:
  - **−21**: the four dedicated test files this story deletes —
    `test_sample_mode_endpoint.py` (8), `test_sample_mode_repository_contract.py`
    (2), `test_sample_mode_ingest.py` (9), `test_sample_mode_end_to_end.py` (2);
    8+2+9+2 = 21.
  - **−1**: `test_dynamo_sample_mode_repository_lifecycle`, removed from
    `test_dynamo_adapters.py` (the file itself stays — it still covers the
    other eight DynamoDB repositories).
  - **+1**: AC1's new `test_run_periodic_records_same_observations_with_
    ingest_decorator_removed` (`test_pull_loop.py`).
  - **+1**: AC6's new `test_the_removed_sample_route_is_gone_and_no_other_
    route_changed` (`test_zone_layout.py`).
  - −21 − 1 + 1 + 1 = **−20**. 851 − 20 = **831**, matching the measured
    after-count exactly.
- 2026-08-16 (fix round): **AC11's gate record corrected.** A commit message
  had claimed "gate 9/9 at `592c76d`" — true when written, but two commits
  before this story's actual final HEAD at the time (both reviewers re-ran
  the backend commands at `69c1a50` and got green, so only the recorded
  commit was stale, not the substance). Also fixed in this same fix round:
  the missing AC11 accounting above (spec FAIL), `docs/project-history.md`'s
  stale "sample_mode is inert, removal is STORY-155" claim (MAJOR — the
  sibling of the identical claim `592c76d` already fixed in `CLAUDE.md`),
  and a false port count (`canonical-types-and-ports.md`'s "ten" — actually
  eleven — that this story's own AC9 pass restated instead of catching).
  Full 9-command gate re-run **9/9 PASS at `787e165`** (this fix round's own
  final HEAD before this entry, which adds no code/gate-relevant change):
  `pytest` 831 passed / 0 skipped, import-linter 9/9 KEPT, `ruff check`/
  `ruff format --check` clean, `cfn-lint` clean, `npm test` 49 files/334
  tests, `npm run build`/`npm run lint` clean, `yt_selftest.py` 113 tests
  OK. Wiki sweep CLEAN, re-run after every commit in this round.
