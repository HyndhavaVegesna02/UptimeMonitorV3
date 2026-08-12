---
title: Zone-rule catalogue — the compile record (history of [[zone-rules]])
tier: reference
verified_sprint: sprint-69
# tier: reference (2026-08-12). Split out of `zone-rules.md`, which was 1502 lines — 24% of
# the whole wiki and its largest staleness surface. This half is the append-only compile
# record: what each sprint re-read, which Facts were rewritten and why, which mutations were
# run, which claims turned out false. It is a record of PAST verifications, so it cannot rot:
# every entry is anchored to the commit and sprint it describes, and a later code change does
# not make "sprint-68 re-read this and found X" untrue.
#
# It declares NO code_refs and carries NO `## Facts` section, per the reference tier. The
# entries below DO contain file paths and old shas; they are citations INTO HISTORY, naming
# what a file looked like at a named commit, never a claim about HEAD. Any claim about the
# code as it stands now belongs in [[zone-rules]], which is swept.
#
# What did NOT move: the rule statements, the compliant/violating citations, the Coverage
# verdicts and the whole `## Adjudication` table all stayed in [[zone-rules]]. Those are live
# claims about live code and must keep paying for the sweep. The ZR-1..ZR-8 sections interleave
# live citations with rationale line by line, so splitting THOSE would have risked moving a
# Fact out of the swept surface — which the protocol forbids. The `## History` boundary is the
# one place the split is clean.
---

This is the history half of [[zone-rules]]. Read that article for what the rules ARE and
whether they are enforced; read this one for how each conclusion was reached and what was
already tried.

`backend/tests/test_zone_rules_enforced_by_claims.py` parses the `## Adjudication` table in
[[zone-rules]] and stops at the next `##` heading, so it never read this section — moving it
here changes nothing that guard can see.

## History

- sprint-68 (STORY-215 third fix round, `verified_sha` bumped `b887883` -> `6ba2558`,
  named Facts re-read): the sweep flagged this article STALE again — `scripts/seed_topology.py`
  changed since `b887883` (the second fix round's comment reword, `7cd1d19`, +1 net line).
  `git diff --stat b887883..8da2f2e` across every file in this article's `code_refs`
  confirms `scripts/seed_topology.py` was the ONLY one that changed — so this article's
  sole affected Fact is the "fifth site" `scripts/seed_topology.py:25` `CONFIG_DIR` bullet
  above. Re-read directly against both the commit it makes a historical claim about and
  HEAD: the pre-fix claims (`os.environ.get("CONFIG_DIR", "config/apps")` at `:25`,
  `load_settings` imported at `:20`, called at `:34`) are frozen citations into `b887883^`
  and still read exactly that at that commit — the comment reword landed after AC4's
  restructure and never touched that earlier commit. The current-state claim ("now calls
  `load_settings()` first and uses `settings.config_dir`") is still true at HEAD too
  (`settings = load_settings()` at `:28`, `config = load_config(settings.config_dir)` at
  `:32`, both one line further down than at `b887883` itself — `:27`/`:31` — because of
  the SAME comment reword). That claim is prose, not a bare line citation, so it needed
  no text edit; only the frozen pre-fix historical citations above (`:25`, `:20`, `:34`,
  into `b887883^`) would have needed correcting had the comment reword touched anything
  before them in that earlier commit, which it didn't. No
  Fact changed; only this one block was re-read, so `verified_sha` moves to `6ba2558`
  (this fix round's own last commit) rather than being bumped blindly over the rest of
  the article.
  Also corrected, in the same commit: the `tools/citation_sweep.py` count section above
  ("A recorded limitation...") still read **27 failures / Twenty bare-filename mentions**
  — stale by one, because the immediately preceding fix round's own AC5-vacuity bullet
  added a further bare-filename mention (`test_demo_fleet_config.py:219-232`) without
  re-running this count afterward. Re-run: **28 failures, Twenty-one bare-filename
  mentions** (2 memory-file + 21 bare-filename + 5 anchor-heuristic = 28); the missing
  citation added to the named list. This is the same "count must be re-derived after the
  prose that changes it" lapse this section already calls out against every fix round
  since STORY-199 — now caught one fix round after it happened, not immediately.
- sprint-68 (STORY-215 second fix round): quality review returned two MAJORs against
  the bullet immediately below (the one written to document C3's third failure),
  both **verified against source before this fix landed**. This is a prose-only
  correction — no code changed, so no RED/GREEN evidence gate applies here; the
  two corrections are inline within that bullet (marked `**Corrected...**`), plus
  a clarifying clause on the AC5-vacuity bullet further down. Summary of what was
  wrong and what is now true, both re-derived against HEAD after the edit:
  (1) that bullet's closing line claimed `verified_sha` changed to "this commit's
  own parent" — `git show c752c14 -- docs/scrum/wiki/zone-rules.md` shows no
  `verified_sha` line touched at all; it is corrected to state plainly that
  `verified_sha` stays `b887883`, unchanged, and why that stamp is still accurate.
  (2) that bullet's shift arithmetic said `935cd70` alone shifted the six stale
  citations by +1; the real shift is +2, cumulative across two stories — STORY-203's
  own `1d43b1b` shifted them +1 first (before STORY-215 touched the file), and
  STORY-203's own wiki commit (`37d20c0`) then stamped `verified_sha` straight onto
  `1d43b1b`, the very commit that had just broken them; `935cd70` added the second
  +1. Corrected to name both stories and both shifts, not STORY-215 alone.
- sprint-68 (STORY-215 fix round): **MAJOR — the `verified_sha` bump in the STORY-215
  landing commit (`7fb87fe`) certified a ZR-3 Fact this same story's own earlier commit
  (`935cd70`) had already made false, and the false Fact was STILL false at the sha the
  bump pointed to (`b887883`), not merely stale by the time it was read.** The "second
  compliant citation" Fact claimed `env_matrix.py` "imports all SEVEN" and `harness.py`
  "imports only the FOUR" it re-types as a dict key, at six named sites. At HEAD (and at
  `b887883`, since `935cd70` is its ancestor): `settings.py` declares NINE `<NAME>_VAR`
  constants (not seven — `935cd70` added `DYNATRACE_ENV_URL_VAR`/`DYNATRACE_API_TOKEN_VAR`
  in the SAME commit), `env_matrix.py` imports all nine, and `harness.py` imports FIVE
  (not four — `DYNATRACE_ENV_URL_VAR`), at SEVEN re-type sites (not six), none of which
  the six OLD cited line numbers (`:546`, `:615`, `:743`, `:749`, `:750`, `:751`) still
  point at, and the true shift is **+2, cumulative across two stories, not the +1 a
  prior version of this very bullet attributed to `935cd70` alone.** Re-derived by
  walking each site through three commits — `1210374` (STORY-202, the numbers as
  originally cited and correct), `1d43b1b` (STORY-203's own harness.py import-block
  edit), and HEAD (`935cd70`, STORY-215's import-block edit):
  `:546`->`:547`->`:548`, `:615`->`:616`->`:617`, `:743`->`:744`->`:745`,
  `:749`->`:750`->`:751`, `:750`->`:751`->`:752`, `:751`->`:752`->`:753` — every site
  shifted +1 at `1d43b1b` and +1 again at `935cd70`. **`1d43b1b` predates STORY-215
  entirely**: `git show 1d43b1b:tools/demo_loop_gate/harness.py | sed -n '546p'`
  prints `f"API (uvicorn) subprocess launched, pid={api_proc.pid}, "` — not the
  CONFIG_DIR re-type site — so these six citations were already false the moment
  STORY-203's `1d43b1b` landed, before STORY-215 touched the file at all. **And
  STORY-203 stamped `verified_sha` over that falseness itself**: its own wiki
  blast-radius commit, `37d20c0`, bumped `verified_sha` straight to `1d43b1b` —
  the very commit whose edit had just shifted these six sites — without noticing
  the untouched "second compliant citation" Fact's six line numbers no longer
  pointed at what they claimed. This is not solely STORY-215's doing: STORY-215's
  `935cd70` added the second +1 on top of a Fact STORY-203 had already broken and
  already certified as re-read. Because `yt_wiki.py`
  computes staleness as git arithmetic against `verified_sha`, bumping it to `b887883`
  told the tool the ENTIRE article had been re-read against that sha, so the sweep
  reported CLEAN over a Fact that was false at that exact sha — the same defect class
  as STORY-204's MAJOR 2 (an article re-stamped over a Fact the implementer had already
  flagged as wrong), and the third instance of it this sprint. **Fixed**: the "second
  compliant citation" Fact rewritten to NINE/FIVE with all seven re-type sites
  re-derived directly against HEAD (`:548`, `:616`, `:617`, `:745`, `:751`, `:752`,
  `:753`); the "Fixed and guarded (STORY-203)" Fact's own two stale spans corrected
  (`harness.py`'s blocklist `:761-774`->`:762-775`; `env_matrix.py`'s `Settings.aws_region`
  site `:50`->`:52`, further shifted by `935cd70`'s two added imports;
  `failure_path_reality_gate.py`'s site untouched, still `:150`); and three more stale
  citations this same commit's line-shifts produced, found by re-deriving the WHOLE
  ZR-3 section rather than spot-fixing only the ones named — `env_matrix.py:82,84`
  corrected to `:84,86`, `harness.py:615` corrected to `:616` (both in the main
  STORY-215 History bullet below), and `test_demo_fleet_config.py:174`/`:206-212`
  corrected to `:194`/`:226-232` (the AC5 mutation citations, shifted by the SAME
  story's separate `61152a3` commit, +20 net lines). **Re-verified, not re-stamped
  blindly, this time**: every `file:line` citation in the ZR-3 section was re-opened
  and its content read directly against HEAD before this bullet was written — see the
  full re-derivation list in the STORY-215 implementer's report. Also re-checked (not
  re-stamped): `demo-engine.md`, the other article `7fb87fe` bumped `verified_sha` on —
  no content-affecting drift found; see that article's own History for what was
  actually re-read. **A CLEAN `yt_wiki.py sweep` after this fix is evidence only that
  `verified_sha` is not behind — it is not evidence any Fact is true; that can only
  come from actually re-reading the cited lines, which is what this bullet records
  happening.** `verified_sha` is **NOT changed by this commit (`c752c14`)** — it
  stays `b887883`, set by `7fb87fe`. That stamp remains accurate for what it
  actually certifies (code drift, not prose correctness): `git diff b887883
  c752c14 --stat` touches only `docs/scrum/wiki/demo-engine.md`,
  `docs/scrum/wiki/zone-rules.md` and `.scrum/sprint-current.yaml` — no file in
  this article's `code_refs` changed between `b887883` and this commit, so the
  sha is still the right one to diff FROM. What `b887883` never certified, and
  what re-bumping it here would have wrongly implied, is that the Fact's PROSE
  was correct — it was false at `b887883` itself (per the MAJOR above), and this
  bullet fixes that falseness by re-reading the cited lines, not by moving the
  sha.
- sprint-68 (STORY-215): **Closed STORY-202's remainder — the two `DYNATRACE_*`
  env-var NAMES, plus a third and fourth `CONFIG_DIR` reader the sweep cannot see at
  all.** `DYNATRACE_ENV_URL_VAR`/`DYNATRACE_API_TOKEN_VAR` promoted in `settings.py`
  (same `<NAME>_VAR` convention as the other seven), and `load_live_secrets` now reads
  through them; `tools/demo_loop_gate/env_matrix.py:84,86` and `harness.py:616` (a
  dict-key literal inside a `print`, not the f-string's own `"DYNATRACE_ENV_URL="`
  text, which does not match) import the constants instead of re-typing them —
  `grep -rn '"DYNATRACE_ENV_URL"\|"DYNATRACE_API_TOKEN"' tools/` now zero hits.
  **Corrected in the STORY-215 fix round: this bullet originally read `:82,84` and
  `:615`** — the commit message's own line numbers for the PRE-fix literal sites;
  this same commit's import-block insertion (+2 lines in `env_matrix.py`, +1 in
  `harness.py`) had already shifted the FIXED sites to `:84,86`/`:616` by the time
  this commit landed, so the bullet was wrong from the moment it was written, not
  merely stale by the time of this fix round.
  **Sweep count, re-derived at this story's own start commit and again after each
  edit:** 9 (start, matching STORY-203's post-fix count) -> 12 with ONLY the two
  constants declared and `tools/` left un-fixed (`test_zr3_sweep_finds_no_
  unadjudicated_collision` went RED, naming exactly the three sites above — no more,
  no fewer) -> 9 again once `tools/` was fixed in the same commit. Landing both
  together is why the net is 9 -> 9, not a story that appears to leave the guard
  broken. Adding the import line to `harness.py`'s existing `from
  src.composition.settings import (...)` block re-keyed the two surviving
  `INDEPENDENT` entries it had already re-keyed twice this sprint (STORY-202 then
  STORY-203): `:927` -> `:928`, `:988` -> `:989`; re-keyed in
  `test_zr3_duplicate_declarations.py`, reason text preserved, both ZR-3 guard tests
  re-verified green.
  **A fourth `MUST-IMPORT-FROM-SRC`-shaped site was found that this rule's own sweep
  cannot see and never adjudicated**, because `tools/zr3_duplicate_sweep.py:209-211`
  scans only `backend/src/` (declaring side) against `tools/` (consuming side) —
  `backend/tests/test_demo_fleet_config.py:163-164,168-169,199-202` re-typed
  `"CONFIG_DIR"`/`"DYNAMO_ENDPOINT_URL"`/`"STATUSPAGE_PAGE_ID"`/`"STATUSPAGE_API_KEY"`
  as literals in the `create_app()` publish-safety pair (STORY-176), the last two
  being the credential-name drift the "why only two rules were mechanised"
  paragraph below already names among ZR-3's credential-safety drift risk. Fixed by
  importing `CONFIG_DIR_VAR`/`DYNAMO_ENDPOINT_URL_VAR`/
  `STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR` — invisible to the sweep either
  way, so this fix is verified by AC5's mutation, not by a sweep count.
  `backend/tests/test_settings.py:30` (`assert CONFIG_DIR_VAR == "CONFIG_DIR"`) is
  the PIN, not a duplication, and was left untouched — a test asserting a constant's
  value is protection; a test re-typing the name to consume it is drift.
  **A fifth site, also outside the sweep's two scanned trees**:
  `scripts/seed_topology.py:25` read `CONFIG_DIR` via its own
  `os.environ.get("CONFIG_DIR", "config/apps")`, independently declaring both the
  name and the default a third time. Now calls `load_settings()` first and uses
  `settings.config_dir`; confirmed at execution that `load_settings` was already
  imported (`:20`) and called (`:34`), so this was a re-order, not a new dependency
  — the AC's escape hatch for an import obstacle did not apply and was not used.
  **AC5's two-sided mutation (renaming `CONFIG_DIR_VAR`'s VALUE in `settings.py`,
  run pre-fix in an isolated `git worktree` with `PYTHONPATH=<worktree>/backend`,
  `module.__file__` printed to prove the worktree tree ran):**
  `test_demo_fleet_config.py:194` (the demo-side assertion) went RED —
  `statuspage_mapping() = {'http-check': 'xdnywbx77npw'}`, delegate type
  `BestEffortPublisher` — a WORKING detector, not rescued by this story's fix; while
  `test_demo_fleet_config.py:226-232` (the live-side assertion) stayed GREEN, because
  its own literal sets `CONFIG_DIR=config/apps`, which is also the resolved default
  when the renamed var is unset — passing for the wrong reason regardless of what the
  variable is called. That vacuity is what the site-3/site-5 fixes above close **for
  the rename mutation** — AC5's definition of the fix. It is **not closed
  intrinsically**: with `CONFIG_DIR_VAR`'s setenv line deleted entirely,
  `load_settings()` resolves the unset var to its own default, `"config/apps"`,
  which `load_config` reads into the same `{'http-check': 'xdnywbx77npw'}` mapping
  `LIVE_CONFIG_DIR` (`config/apps`, absolute) also yields — so
  `test_demo_fleet_config.py:219-232` still passes with that line gone. No
  constant substitution can fix this; the test would have to assert against a
  `CONFIG_DIR` value that DIFFERS from the default to stop passing vacuously.
  **Corrected in the STORY-215 fix round: this bullet originally read `:174` and
  `:206-212`** — the exact lines at the pre-fix (`61152a3^`) commit the AC5 mutation
  ran against, which this bullet copied forward uncorrected even though the same
  story's own `61152a3` (AC3, +20 net lines to this file's docstring and import block)
  had already shifted them to `:194`/`:226-232` by the time this bullet was written.
  **No claim that the tools<->src name boundary is now fully closed**: this rule's
  own sweep is structurally blind to `backend/tests/` and `scripts/`, so a future
  re-typed name in either tree would not be caught by `test_zr3_sweep_finds_no_
  unadjudicated_collision` — only by a mutation proof like AC5's, which is not a
  standing guard (`ZR-5`'s STORY-209, sprint-69, is the nearest planned mechanisation,
  and it is scoped to `CONFIG_DIR` parity between the two composition roots, not a
  general `backend/tests/`/`scripts/` sweep widening). Added
  `backend/tests/test_live_secrets.py` to `code_refs` (it now holds the
  `DYNATRACE_*_VAR` pin this article's Compliant-citation reasoning depends on).
  verified_sha -> b887883 (this article's content commit is the direct child of
  that sha, the same self-reference gap STORY-197/199/202/203/205 hit before it).
- sprint-68 (STORY-203): **Fixed and guarded ZR-3's last four `MUST-IMPORT-FROM-SRC` entries;
  zero remain.** `env_matrix.py:49` and `failure_path_reality_gate.py:149` (pre-fix line
  numbers; each fix's own import-block edit shifted the line by +1, to `:50`/`:150` at HEAD)
  each hardcoded `Settings.aws_region`'s `"us-east-1"` default a second time; both now import
  `Settings` and reference `Settings.aws_region`. `harness.py:754`/`:757`'s defensive blocklist hardcoded
  `Settings.dynamo_observations_table`/`dynamo_control_table`'s defaults; fixed on the
  blocklist's RIGHT-hand side only (the LEFT stays the real `api_env` read) — replacing the
  LEFT-hand side too would turn the check into a tautology disconnected from the environment
  it exists to guard, demonstrated by mutation:
  `test_harness_assertions.py::test_assert_ac1_preconditions_blocklist_does_not_fire_on_fresh_table_names`
  went RED under that exact mistake (a bare `AssertionError` where `httpx.HTTPError` was
  expected), reverted, `git diff` empty. Adding `Settings` to `harness.py`'s existing import
  block shifted two surviving `INDEPENDENT` entries by +11 lines (`:910`->`:921`,
  `:971`->`:982`); re-keyed, reason text preserved. Sweep count: 13 -> 9 (re-derived at HEAD
  both before and after); the remaining 9 are all `INDEPENDENT`.
  **AC4's fifth, cross-representation case (`store.py`'s `VENDOR_HEALTH_WINDOW`, invisible to
  this sweep's literal-equality comparison) was a DECISION, not a fix**: its existing
  wire-contract justification (the window is part of the vendor wire contract the demo engine
  answers, not borrowed from `adapters/inbound/dynatrace/query.py`'s `HEALTH_CHECK_WINDOW`) is
  upheld, and `test_zr3_duplicate_declarations.py`'s entry rewritten from
  `MUST-IMPORT-FROM-SRC ... Fix: STORY-203` (which would have pointed at this same, now-closed
  story as an outstanding fix) to `INDEPENDENT`, citing
  `test_vendor_health_query.py::test_vendor_health_window_matches_the_composition_health_check_window`
  as the mechanical pin against silent divergence, rather than arguing from the docstring
  alone. **AC6 mutation proof (re-run for this article):** re-introduced the fixed
  `harness.py` duplicate (reverted the blocklist's right-hand side back to the literal
  `"uptime-observations"`) — `test_zr3_sweep_finds_no_unadjudicated_collision` failed, naming
  `tools/demo_loop_gate/harness.py:762` exactly; reverted, `git diff` empty. Rewrote the ZR-3
  Fact bullet (the "genuine, adjudicated violation" paragraph, now past tense), the Measurement
  bullet's stale present-tense "violation" reference, and the adjudication table row (all four
  `MUST-IMPORT-FROM-SRC` fixed, zero remain). Added `backend/tests/test_zr3_duplicate_declarations.py`
  and `backend/tests/demo_loop_gate/test_harness_assertions.py` to `code_refs` (both now hold
  Facts this article cites by name, the same reason `test_vendor_health.py` was added at
  STORY-204). verified_sha -> `1c07def` (this article's content commit is the direct child of
  that sha, the same self-reference gap STORY-197/199/202/205 hit before it).
- sprint-68 (STORY-203 fix round): a quality-review minor asked for a named failure message on
  each of the AC1(b) blocklist asserts (`harness.py:761-774` at HEAD, widened from `:761-768`) —
  every other assert in `_assert_ac1_preconditions` already carried one. That edit added lines
  inside the function, shifting the two `INDEPENDENT` entries the bullet above re-keyed to
  `:921`/`:982` a further +6 lines each, to `:927`/`:988`; re-keyed again in
  `test_zr3_duplicate_declarations.py`, reason text preserved, `test_zr3_adjudications_are_still_current`
  and `test_zr3_sweep_finds_no_unadjudicated_collision` both re-verified green. **This fix round
  also missed constraint C3 once**: `zone-rules.md`'s ZR-3 update (this article, `3ab9c9b`) landed
  after the code fixes it describes (`e9cb8c8`, `691227f`, `db949c8`) and after `1c07def`'s own
  ledger rewrite — at least two committed states (`92241bd`, `1c07def`) carried this article still
  asserting a live violation the tree had already fixed. Recorded plainly in
  `docs/scrum/stories/STORY-203-tools-import-shared-literals.md`'s History per PO direction; not
  rewritten, and AC7 is not claimed MET. verified_sha -> `b68165c` (this article's content
  commit is the direct child of that sha, the same self-reference gap noted above).
- sprint-68 (STORY-204 third fix round): the second fix round fixed the `query.py:133`->`:136`
  single-point citation (below) but missed a DIFFERENT stale pattern in Finding 2's own body: the
  `build_vendor_health_dql` whole-function citation, `query.py:136-155`, was that span BEFORE the
  fix round's 3-line "PUBLIC" comment insertion and needed the same +3 shift, to `:139-158` —
  corrected below. Found by re-deriving every `query.py` citation in the repo against the real
  file, not by trusting a named list (a named four-site list given for this round was itself
  incomplete). No Fact's substance changed; citation-only. verified_sha -> 81a1351 (this article's
  content commit is the direct child of that sha).
- sprint-68 (STORY-204): **Fixed and guarded ZR-8 Finding 2 — the second and final live
  violation this rule adjudicated.** `composition/vendor_health.py` no longer builds any DQL
  string; `build_vendor_health_query` relocated into
  `backend/src/adapters/inbound/dynatrace/query.py` as `build_vendor_health_dql`, sharing the new
  `_reject_dql_breaking_native_id` helper with `build_dql_query` (extracted from the latter's own
  inline check, not a second copy) — so a `native_id` containing any of the four
  `_DQL_BREAKING_CHARS` now raises `InvalidNativeIdError` identically on both the ingest path and
  the vendor-health probe path, which previously silently built a malformed query. **Shown RED**:
  the new parametrised composition-level test
  (`test_vendor_health.py::test_check_vendor_id_health_rejects_native_id_with_dql_breaking_char`,
  all four breaking characters) failed against real pre-fix HEAD with
  `Failed: DID NOT RAISE InvalidNativeIdError` for every case; green after the fix, no code left
  mutated. Rewrote Finding 2's body to past tense, its Coverage verdict (the guard is stronger than
  the "parallel assertion" shape this article originally proposed — the builder itself is gone from
  composition, not merely checked), the adjudication table row (both findings now
  `ENFORCED-BY`), and the "why only two rules were mechanised" paragraph, which had said Finding 2
  "remains live" — both of ZR-8's findings are now fixed and guarded; no live violation remains
  under this rule. Added `backend/tests/test_vendor_health.py` and
  `backend/tests/test_dynatrace_adapter.py` to `code_refs` (they now hold the guard tests this
  article cites by name, the same reason `test_zone_layout.py` was already a `code_ref` for
  Finding 1's guard). verified_sha -> c815ebe.
- sprint-68 (STORY-205 fix round): RE-VERIFIED, no content change. The sweep flagged
  `backend/src/adapters/persistence/topology_keys.py`, `backend/tests/test_topology_keys.py`
  and `backend/tests/test_zone_layout.py` (all `code_refs`) for four quality-review minor
  fixes: renaming the meta-test `test_seed_dynamo_owns_no_hand_built_topology_key` (this
  article never cited that name — it cites the real standing guard,
  `test_seed_dynamo_uses_shared_topology_key_schema`, which is unchanged); sorting
  `find_hand_built_topology_key_dicts`'s returned line numbers into source order (the
  Fact above only claims the guard "fails, naming the offending line" — true either way);
  making `TOPOLOGY_PK` private (`_TOPOLOGY_PK`, no consumer outside the module and its own
  test); and documenting the guard's blind spots in its own docstring (this article's
  Coverage verdict already says "narrow and per-instance... checks exactly this one file's
  exact shape", which the docstring addition is consistent with, not a correction to).
  Re-confirmed the guard still fires RED and names the offending lines after reintroducing
  a hand-built `pk`/`sk` dict into `seed_dynamo.py`; file restored, `git diff` empty.
  verified_sha -> d9a3f95.
- sprint-68 (STORY-205, sha bump): re-stamped `verified_sha` to `96f9048`. The commit
  that landed the Finding 1 rewrite (`e8768e8`) also touched
  `tools/demo_loop_gate/failure_path_reality_gate.py` (a `code_ref`) in the SAME
  commit, so the sha it could truthfully record (its own parent) was already stale
  the moment it landed — the same self-reference gap this article's own History
  shows STORY-197/199/202 hitting and re-stamping in a follow-up commit each time.
  No content changed here.
- sprint-68 (STORY-204 fix round): **AC7b problem 2 (spec review FAIL).** The adjudication row and
  Coverage verdict cited only the two validation-parity tests, never
  `test_vendor_health.py::test_vendor_health_module_builds_no_dql_string_itself` (AC4) — the guard
  that actually tests ZR-8's own statement ("vendor query-construction logic lives in exactly ONE
  adapter"). Worse, the Coverage verdict positively claimed "there is no DQL string construction
  left in `composition/vendor_health.py` for a guard to police" — false, since that guard exists and
  polices exactly that. Cited it in both the adjudication row and the Coverage verdict; deleted the
  false claim; disclosed the guard's limit (a literal-substring check, proven evadable by a
  re-derived builder using a spliced `fetch` constant, `"|filter "` without the space, and
  `"\n".join(...)` — the dangerous half, missing validation, is still caught by the behaviour
  test). Also updated `test_vendor_health.py`'s own docstring for the same guard, same disclosure,
  in the same commit (STORY-205's AC2 docstring-disclosure shape, applied here). Also fixed the
  run.py/vendor_health.py stale comment (`composition/run.py::main`,
  `composition/vendor_health.py::check_vendor_id_health`) both reviewers independently found — it
  claimed the probe "never raises"/"propagates identically to the ingest path"; recorded the real
  blast-radius asymmetry (ingest degrades one signal via `run_periodic`, the probe aborts `main()`
  entirely). code_refs already covered every file touched. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 fix round, second pass): `_HEALTH_CHECK_WINDOW` made public
  (`HEALTH_CHECK_WINDOW`, an unrelated minor from the same fix round — the only private-**name**
  import across a module AND zone boundary in `backend/src`, under a leading-underscore-*symbol*
  reading). Finding 2's Fact above repointed to the new public name. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 second fix round): fixed a stale line ref (`query.py:133` -> `:136`, moved
  by bfa5f77's added comment lines) in Finding 2's Fact above, and narrowed both "the only
  private-name import" occurrences in this article to the leading-underscore-*symbol* reading they
  actually hold under — `composition/app.py:224` imports the private *package*
  `src.api.v1._shared.errors` across the same kind of zone boundary, which is a private PACKAGE,
  not a private name. No file in this article's `code_refs` changed (prose-only correction).
- sprint-68 (STORY-204 second fix round): the sweep flagged `run.py` again. STORY-204's second fix
  round reordered (did not change the substance of) the vendor-id drift probe's call-site comment
  so its opening line states the fail-fast scope on its own (see [[dynatrace-adapter]]). The
  blast-radius asymmetry this article records (ingest degrades one signal via `run_periodic`, the
  probe aborts `main()` entirely) is unchanged. Re-verified only; no Fact changed. verified_sha ->
  d554227.
- sprint-68 (STORY-205): **Fixed and guarded ZR-8 Finding 1.** `composition/seed_dynamo.py`
  no longer hand-builds the `TOPOLOGY` partition's key schema; it now imports
  `app_item_key`/`component_item_key`/`signal_item_key` from the new
  `backend/src/adapters/persistence/topology_keys.py`, the single module
  `DynamoComponentRepository` and `DynamoSignalRepository` also import for both key
  shapes (item-key dict and boto3 query condition). Added the standing guard
  `backend/tests/test_zone_layout.py::test_seed_dynamo_uses_shared_topology_key_schema`,
  shown RED twice (against the real pre-fix file, and again by a deliberate
  re-introduction post-fix; both reverted). Behavioural drift proof (AC2): the existing
  round-trip test `test_dynamo_seed.py::test_seed_topology_dynamo` is unchanged and,
  unmutated, was already green both before and after — it is evidence only alongside
  two recorded mutations: pre-fix, changing `DynamoComponentRepository`'s own inline
  `"COMPONENT#"` literal alone reddened it (seed and repository diverged); post-fix,
  changing the SAME prefix in `topology_keys.py` (the module both now import) left it
  green — seed_dynamo.py followed automatically, proving the duplication is gone rather
  than relocated. That same post-fix mutation reddened
  `test_dynamo_adapters.py:17,82`'s hand-built seed helpers, as expected (they bypass
  the shared module by design, to test the repositories in isolation) — recorded, not
  "fixed" into silence. Rewrote the Finding 1 paragraph, its Coverage verdict, the
  adjudication table row and the "why only two rules were mechanised" paragraph to
  past/mixed tense; repointed the two already-stale citations
  (`dynamo_component_repository.py`/`dynamo_signal_repository.py` line numbers STORY-199's
  pagination loops had displaced) and `failure_path_reality_gate.py`'s docstring to the
  new schema module. `docs/scrum/wiki/persistence-adapters.md` updated in step (see
  [[persistence-adapters]]). Finding 2 (`vendor_health.py`) is untouched, still
  `GUARDABLE-DEFERRED (STORY-204)`. verified_sha -> a5a2d68.
- sprint-67 (STORY-202 quality-review fix round): **MAJOR — the six `harness.py`
  AC8 site line numbers in the Fact below were the story's own PRE-edit AC8
  numbers** (`:540`/`:609`/`:736`/`:742`/`:743`/`:744`), copied forward despite
  AC8's own warning that this story's edits would shift them. Re-derived against
  HEAD by directly opening each line: `:546`
  (`f"env CONFIG_DIR={api_env[CONFIG_DIR_VAR]!r}"`), `:615`
  (`f"CONFIG_DIR={loop_env[CONFIG_DIR_VAR]!r}"`), `:743`
  (`result["config_dir_api"] = api_env[CONFIG_DIR_VAR]`), `:749`
  (`result["dynamo_endpoint_url"] = api_env[DYNAMO_ENDPOINT_URL_VAR]`), `:750`
  (`result["observations_table"] = api_env[DYNAMO_OBSERVATIONS_TABLE_VAR]`),
  `:751` (`result["control_table"] = api_env[DYNAMO_CONTROL_TABLE_VAR]`).
  Corrected in the Fact above, qualified "line numbers as of `1210374`" per this
  article's existing convention. `backend/tests/test_zr3_duplicate_declarations.py`'s
  `failure_path_reality_gate.py:149` adjudication reason (a separate file, not
  this article, but the same review round) also carried a stale cross-reference
  to `env_matrix.py:39` five lines after the same module's own docstring
  documented that collision re-keyed to `:49` — corrected there too.
  verified_sha -> `1a70f45`.
- sprint-67 (STORY-202 fix round): **the false "both files import all seven" claim
  corrected** (see the Fact above and the entry below) — measured at HEAD:
  `env_matrix.py` imports all seven, `harness.py` imports only the four it
  actually re-types as a dict key. Also landed AC4's two-sided mutation proof
  (rename `CONFIG_DIR_VAR`'s VALUE both at the pre-STORY-202 commit `6f872c3`
  and at HEAD, in an isolated `git worktree` for the pre-fix half, restored and
  `git diff` confirmed empty for the post-fix half): pre-fix, `env_matrix.py`'s
  hardcoded `"CONFIG_DIR"` literal and the renamed `settings.py` DISAGREE — the
  harness's `config/demo` value never reaches `load_settings()`, which silently
  falls back to the `config/apps` default; at HEAD, after the identical rename,
  both sides agree because they read the one shared `CONFIG_DIR_VAR` symbol. And
  re-derived AC9's collision count directly (`python tools/zr3_duplicate_sweep.py`
  at HEAD): **13**, matching the 15-minus-the-two-retired-`env_matrix.py`-entries
  arithmetic this rule's own Coverage verdict predicted — no discrepancy to
  report this time (contrast the earlier "101, not 105" measurement above).
  verified_sha -> `3c0cdeb`.
- sprint-67 (STORY-202): fixed the seven env-var-NAME collisions ZR-3's own
  measurement found in `tools/demo_loop_gate/env_matrix.py` (5) and
  `tools/demo_loop_gate/harness.py` (6, of which 2 — the Statuspage credential
  keys — were the pre-existing adjudicated violations; the other 4 arose ONLY
  because this story's own fix (promoting `settings.py`'s five function-body
  literals to module constants) made them newly-declared shape-i values, per
  `test_zr3_duplicate_declarations.py`'s own module docstring). `env_matrix.py`
  imports all SEVEN constants (it sets all seven as child-env dict keys);
  `harness.py` imports only the FOUR it actually re-types as a dict key
  (`CONFIG_DIR_VAR`, `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`) — it never re-types `AWS_REGION`/
  `STATUSPAGE_PAGE_ID`/`STATUSPAGE_API_KEY` as a literal dict key anywhere, so
  there is nothing there for it to import. Both from
  `backend/src/composition/settings.py` rather than re-declaring the key
  names. (An earlier draft of this History entry and the Fact above both said
  "both files import all seven" — false at HEAD; corrected in the STORY-202
  fix round.) `_ADJUDICATED`'s two `env_matrix.py`
  `MUST-IMPORT-FROM-SRC` entries (`:75`, `:77`) were REMOVED (fixed, not
  displaced); five entries STORY-202's own edits displaced without retiring were
  RE-KEYED with their reason text preserved (`env_matrix.py` `:39`->`:49`;
  `harness.py` `:747`->`:754`, `:750`->`:757`, `:903`->`:910`, `:964`->`:971`).
  Sweep count: 15 -> 13 (the two retired entries); the remaining 4
  `MUST-IMPORT-FROM-SRC` entries are now filed solely to STORY-203 (VALUE
  duplication, not key-NAME duplication — the distinction STORY-202's own scope
  turned on). verified_sha -> `1dc1c73`.
- sprint-67 (STORY-199 fix round, quality review): **FACT CORRECTION, not a bare
  re-stamp.** The ZR-7 finding paragraph stated the hot-path cost backwards: it read
  that `is_under_maintenance` "never scan[s] the rest of the GSI partition on the
  common not-under-maintenance path". That is inverted — early-return-on-match only
  ever saves work on the (rare) under-maintenance path; the not-under-maintenance path
  (the common one, the one `decide` takes every cycle) is the one that reads the
  ENTIRE `MAINT` partition, because `False` is returned only once `LastEvaluatedKey`
  is exhausted. Corrected to state the true, asymmetric cost — the common path is the
  expensive one and it grows with maintenance-window history forever. The
  implementation is unchanged and correct; only this Fact's description of its cost
  was wrong. Also fixed the ZR-7 adjudication row, which named `is_under_maintenance`
  as the method used for the recorded mutation proof when the History entry (and the
  actual evidence) both say `list_components`. verified_sha -> fe8df72.
- sprint-67 (STORY-200 fix round, quality review): **MAJOR — the ZR-6 adjudication row claimed
  mechanical enforcement that does not exist.** It read `ENFORCED-BY
  backend/tests/test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`
  and closed "only this one, now-fixed instance is pinned" — disproved by mutation: reverting the
  ENTIRE ZR-6 fix (port back to `action: str`, fake back to `str`, adapter back to `if action ==
  "approved":`) leaves the full suite at 696 passed, IDENTICAL to HEAD. The named test pins the new
  2-member `{APPROVED, REJECTED}` SUBSET guard; it detects nothing about the port's TYPE. Corrected
  to `FIXED (STORY-200, sprint-67) — NO STANDING GUARD`, stating plainly that the instance is fixed,
  the subset is pinned by that one test, and the port-typing regression itself is unguarded — a
  future story could re-widen the port back to `str` with a fully green gate. Also fixed the
  contradicting "why only two rules were mechanised" paragraph nine lines below the table, which
  still listed ZR-6 as present-tense "blocked behind a fix or a design decision" in the same commit
  that (incorrectly) marked it `ENFORCED-BY`. verified_sha -> 013f344.
- sprint-67 (STORY-200): landed the ZR-6 fix. `record_approval_event`'s port
  signature now types `action: ProposalState` (decision (a), the sibling method's
  type — not a narrower type; the story file's "design decision" section records
  the full reasoning and an explicit expiry condition). The adapter,
  `DynamoProposalRepository.record_approval_event`, now compares by enum identity
  (`action is ProposalState.APPROVED`), with `.value` used explicitly at both write
  sites (the `sk` f-string and the `"action"` item attribute) — `ProposalState` is
  `class ProposalState(str, Enum)`, a str MIXIN not `StrEnum`, so on Python 3.13 an
  f-string over the bare member renders `"ProposalState.APPROVED"`, not
  `"approved"`; omitting `.value` at the `sk` site was confirmed to corrupt every
  approval event's sort key (reproduced as an actual test failure before the fix,
  not just reasoned about). The "3 invalid members" gap is closed with
  `ApprovalService._decide` raising `InvalidApprovalActionError` for any `to_state`
  outside `{APPROVED, REJECTED}` — deliberately NEW validation, since
  `is_valid_transition` admits any non-OPEN target and does not constrain this
  narrower set. Mutation-proven: changing `ProposalState.APPROVED`'s value (not
  its name) trips
  `test_dynamo_proposal_repository.py::test_dynamo_proposal_repository_record_approval_event`
  (the event item becomes unreadable at its expected sort key); restored, `git diff`
  empty. `STORY-198` was subsumed rather than landed separately (both would have
  edited the same three lines twice). verified_sha -> d469d2c.
- sprint-67 (STORY-199): landed the ZR-7 fix. All five findings (`is_under_maintenance`,
  `list_windows`, `list_components`, `list_signals`, `list_open`) now loop on
  `LastEvaluatedKey`; `is_under_maintenance` short-circuits `True` on first match and
  returns `False` only once `LastEvaluatedKey` is exhausted, never on an
  empty-after-filter page. `test_zr7_pagination_guard.py`'s `_EXEMPTIONS` dropped from
  six entries to one (the `dynamo_publication_repository.py:53` `PERMANENT` entry for
  `list_recent`, unaffected). Mutation-proven: removing `list_components`'s loop trips
  both the guard's unexempted-violation check and its own AC2 pagination test; restored,
  `git diff` empty. verified_sha -> 460d3ee.
- sprint-66 (STORY-194): created. Rules ZR-1..ZR-3 covered the PO's five named areas
  ((a) adapter persistence -> ZR-1; (b) core reaching outward -> already mechanical;
  (c) api reaching another feature/an adapter -> already mechanical; (d) vendor
  vocabulary escaping its adapter -> ZR-2; (e) the `tools/` <-> `backend/src/`
  duplicated constant -> ZR-3).
- sprint-66 (STORY-194 fix round, spec FAIL on AC5 + 5 quality MAJORs + 9 minors):
  ZR-2 rewritten FORM-based (three closed compliant forms, closed forbidden-form set,
  the provenance carve-out, the six previously-unadjudicated citations settled, the
  vendor-word list demoted to an explicitly non-exhaustive guard detection seed).
  ZR-1's contract sketch narrowed to the enumerated persistence/repository port
  modules (excluding the `signal_ingest` front door). ZR-2's guard sketch extended to
  name `Attribute`/`keyword`/`Constant` node coverage and its stated residue. ZR-3
  pinned to module-level UPPER_CASE constants (101-vs-0 measurement recorded, with a
  note that the pre-fix-round figure of 105 did not reproduce), the import-edge
  exemption replaced with a runtime-import exception, and a real violation
  (`tools/demo_loop_gate/harness.py:746-750` vs `backend/src/composition/settings.py:21-22`)
  adjudicated rather than left as an illustration. ZR-4 (five-file convention) and
  ZR-5 (composition-root parity) added for STORY-196 AC4/AC5. Nine minors applied:
  the STORY-190 counterfactual moved to Inference; ZR-3 given one operative verdict;
  the vendor-vocabulary source correctly split across concrete rules 1 and 3; the
  "only composition sees both sides" claim given its precision parenthetical; ZR-2's
  stated scope widened to match its guard's actual scope (`queries`, package root);
  ZR-1's coverage verdict named the RED-proving mutation; the zone-wide-negative
  caveat added; the `signal.py` citation corrected to `:5-6`.

- sprint-66 (STORY-194 acceptance, orchestrator correction 2026-07-31): ZR-3's pinned
  SCOPE was internally inconsistent with its own adjudicated violation. The scope covered
  only shape (i) (module-level UPPER_CASE constants) on both sides, but the violation it
  adjudicates is a function-body literal in `tools/demo_loop_gate/harness.py:746-750`
  duplicating a pydantic FIELD DEFAULT at `backend/src/composition/settings.py:21-22` —
  neither side in scope. That is also why the narrow measurement returned 0 while a real
  duplicate stood. Corrected in three places (Statement, Measurement, Coverage verdict):
  the `backend/src/` side now covers both declaration shapes, and the `tools/` side counts
  literals inside function bodies. Consequence for STORY-196 AC3: the sweep MUST find the
  `harness.py` case, and a sweep reporting 0 while that case stands is a broken sweep, not
  a clean tree. Neither reviewer could have caught this — it emerged from the fix round's
  own scope-pinning.

**AC3 citation-resolution sweep, rebuilt to EXTRACT from the article (not a
hand-typed manifest) — command and full output recorded in the story file's
History**, per the fix round's re-verification requirement.

- sprint-66 (STORY-195 quality-review fix round, 2026-07-31): added `ZR-6` and `ZR-7`,
  neither anticipated at STORY-194 planning. An independent audit of STORY-195's own
  footprint (46 of the 58 files it read) found: (1) STORY-195 had verdicted
  `core/ports/proposal_repository.py` `CLEAN` while separately quoting its own
  `action: str` line as the explanation for an adapter-level "catalogue gap" (`GAP-1`)
  — the port signature leaking a primitive where `ProposalState` already exists and is
  used correctly one method away is the ROOT CAUSE, not the adapter's literal
  comparison, and is now scored as its own `ZR-6` finding (`MAJOR`); (2) a genuine,
  unreported production defect — `dynamo_maintenance_repository.py::is_under_maintenance`
  and four sibling `list_*` methods pair an unbounded DynamoDB `query` with a
  post-read filter/no loop, silently truncating past a 1 MB page against a port
  contract that promises "all" — now `ZR-7` (`MAJOR`). Both rules are `GUARDABLE`
  only partially, with the false-positive risk stated honestly in each rule's own
  Coverage verdict, per the same discipline ZR-1/ZR-2/ZR-3 already established. Full
  detail, the fix stories these findings were filed as, and the re-derivation
  commands are in `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`.
  Also corrected in passing (found by the fix round's strengthened, content-anchor
  citation sweep — see that report §7): the ZR-3 measurement note's bare-filename
  citation for the `settings.py` field defaults (no directory prefix) widened to the
  full repo-relative `backend/src/composition/settings.py:21-22`, matching this
  article's own full-path convention everywhere else.

- sprint-66 (STORY-196 quality-review fix round, 2026-07-31): added `ZR-8`, from an
  independent audit of STORY-196's own footprint (all 13 `composition/` modules,
  `api/dependencies.py`, six `service.py` files, and the `tools/` boundary crossers)
  that found the audit's biggest miss: `composition/seed_dynamo.py` hand-builds the
  SAME DynamoDB key schema `DynamoComponentRepository`/`DynamoSignalRepository`
  already own — raw `boto3` persistence from the composition zone, a third
  declaration of one schema on the boot path of both composition roots, which had
  already drifted once (`tools/demo_loop_gate/failure_path_reality_gate.py:163-172`'s
  own docstring records it) and which `docs/scrum/wiki/persistence-adapters.md`
  already treats as adapter-adjacent in its own Facts. STORY-196's original report
  had verdicted `seed_dynamo.py` `CLEAN` under a false generalisation ("pure wiring —
  every branch routes to a named core service/query/domain type"), which is untrue of
  `seed_dynamo.py` (routes to `boto3`'s Table API) and of `composition/dynamo.py`
  (routes to `boto3.resource`) alike — the SAME bulk-`CLEAN`-overstatement class
  STORY-196's own report criticises STORY-195 for. `ZR-8` generalizes `GAP-2`
  (`composition/vendor_health.py` duplicating a DQL query builder without its
  validation, STORY-196's original finding) and this new `seed_dynamo.py` finding
  under one statement: storage/vendor mechanics live in exactly one adapter: another
  zone calls it rather than re-implementing it — legal by every one of the eight
  `lint-imports` contracts, since they check import edges, never reuse-vs-rederive.
  Filed as `STORY-205`. Full detail and re-derivation commands:
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md`.
- sprint-69 (STORY-206, verified_sha bumped `6ba2558` -> `b8e22d2`): ZR-1's adjudication row
  flips `GUARDABLE-DEFERRED (STORY-206)` -> `` `ENFORCED-BY inbound-adapters-dont-persist` ``. The
  ninth `lint-imports` contract (`pyproject.toml`) is now real, shown RED by mutation and reverted
  (`git diff` empty) — see the row for the exact command output. Contract count of record moves
  8 -> 9 throughout this article's own general/current-tense prose (title, Purpose, ZR-6/ZR-7/ZR-8
  "why the contracts pass it" Facts, the closing Inference paragraph); the legend's "existing eight
  DoD commands" phrase (a DoD-COMMAND count, not a contract count) is unchanged by design, and
  dated History entries above keep whatever count was accurate at the sprint they describe. The
  Purpose section's STORY-190 example ("passed all eight ... that existed at the time") is likewise
  left as a historically-accurate count with a forward pointer to this story, rather than bumped to
  a now-false "passes all nine." `forbidden_modules`' own completeness (a newly added port appended
  in the same commit) remains hand-maintained until STORY-220 (sprint 70) — the row states this.
- sprint-69 (STORY-206 rework, quality review MAJOR-1/MINOR-3, verified_sha unchanged at
  `b8e22d2` — no code_ref moved, only this article's own prose was corrected): ZR-1's Coverage
  verdict stated the exact-module-import constraint positively for the first time — the package
  form (`from src.core.ports import SignalIngestPort`) is not itself forbidden but trips the
  contract today only because `core/ports/__init__.py`'s re-exports make it transitively import
  all nine forbidden modules at once; proven by mutation both directions (`8 kept, 1 broken` ->
  `9 kept, 0 broken`), both reverted, `git diff` empty. The adjudication row's single stated
  residue became TWO: the pre-existing hand-maintained-list residue is kept verbatim (not
  weakened — the PO's STORY-220 approval was conditioned on that sentence), and a second residue
  is added naming the exact-module-form dependency as a real, if currently harmless, gap. Also
  fixed: the Coverage verdict's "STORY-197 can show this RED... " was future tense and
  misattributed the mutation to STORY-197 (ZR-1's completeness-test story) rather than STORY-206
  (the story that actually ran it) — corrected to past tense, attributed to STORY-206.
