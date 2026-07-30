# Sprint 64 retro — 2026-07-30

**Outcome:** 8/8 accepted, no blocked stories, one fix round. Estimate accuracy held after the
pre-lock re-point (STORY-182 3 → 5; it consumed its 5).

This retro inspects the *process*. The sprint's subject happened to be "make proofs that can
actually fail", and the process failed in exactly that way twice — once in a story, once in my own
spike. That is the thread.

---

## What worked, and should not be quietly dropped

**Pre-lock verification paid for itself, twice over.** `yt-plan-verifier` returned GAPS with 8
blocking findings. Two of them would have wrecked the sprint mid-flight: AC3/AC4 were
*unsatisfiable* with the checked-in scenarios (6 of 41 signals covered), and the publish-guard
reality gate *could not come back negative* (`build_publisher` returns the same top-level type on
both branches). Neither is the kind of thing an implementer discovers cheaply on day 3.

**The 0-point spike was the best-value item in the sprint.** It cost one orchestrator turn and it
(a) confirmed the fleet-coverage fix works, (b) cut the authoring cost from ~39,000 rows to 820, and
(c) found a field-name trap by *making the mistake itself*. Two of the plan's blocking findings were
~20 minutes of reading away — without the spike they land on day 4 with the budget spent.

**The reviewer pair earned its cost on the 5-pointer.** Spec FAIL + quality FIX_REQUIRED, four
majors, two of which corrected the orchestrator directly. A 5-point story with a safety-critical
path is exactly where the pair belongs.

**A5 worked on its first real use.** Both reviewers died mid-read on a session limit with no verdict.
That was recorded on the board and relaunched, rather than quietly retried or waved through.

---

## Amendment A6 (proposed) — a green `pytest` must not hide a skipped floor

**The incident.** Establishing the sprint baseline, `pytest` exited **0** at `561 passed, 53 skipped`
and `yt_gate.py` recorded **PASS**. Docker was down, so `conftest.py`'s `dynamo_local` fixture
skipped every DynamoDB-gated test. With the container up, the same commit and the same command gave
`614 passed, 0 skipped`. **53 tests — the entire persistence floor — vanished with no red signal and
no difference in exit code.**

We worked around it all sprint by hand: recording pass/skip counts on every gate record and treating
a nonzero skip count as an incomplete gate. That is prose, applied by memory, and it is the lowest
rung. It held only because one person happened to notice the count.

**Why this is worth a rung.** The DoD is "the non-LLM floor". A floor with a silent hole exactly the
shape of "Docker wasn't running" is not a floor. And the failure is invisible in precisely the
situation where it matters most — CI, a fresh machine, a reviewer's environment.

**Proposed rung — project code, not prose.** An opt-in strictness switch in `backend/tests/conftest.py`:
when `REQUIRE_DYNAMO=1` is set, the `dynamo_local` fixture **fails** instead of skipping. The DoD
then annotates the `pytest` command with the existing generic `(requires-env: REQUIRE_DYNAMO=1)`
mechanism `yt_gate.py` already supports (added at the sprint-47 retro), so the gate refuses to run a
DynamoDB-blind `pytest` at all rather than passing one.

Fallback if that proves awkward: a `pytest_sessionfinish` hook that errors on any skip when the env
var is set. Either way the enforcement lives in code, and the prose rule retires.

---

## Amendment A7 (proposed) — a reality gate is an exit code, not a paragraph

**The incident.** STORY-182's positive-side harness computed every AC3/AC4/AC5 value correctly and
**printed** them. It asserted only AC1. `__main__` dumped JSON and exited **0 regardless**, and a
polling timeout set a flag and *continued* rather than failing. I ran it, read the numbers, saw they
were right, and reported "reality gate side 1 PASS" to the PO.

The numbers *were* right. But the artifact could not have told me otherwise. On a rerun with a dead
monitor id or a non-empty approvals list, it would have printed the bad value and exited 0 — and my
report would have been identical.

**This is A1/A3's own failure mode, one level up.** A1 asks "how could this have failed?" and A3 asks
"did the sides differ?" — both about the *subject* of the proof. Neither asks whether the *harness*
is capable of returning failure at all. Sides 2 and 3 got this right on their own
(`sys.exit(0 if main() else 1)`); side 1 did not, and nothing caught the inconsistency until spec
review.

**Proposed rung — checklist, with a mechanical anchor on the board.** Two lines:

- *Implementer checklist:* any reality-gate or discrimination artifact must terminate with an
  explicit verdict and a **non-zero exit on failure**. An artifact that only prints is a report, not
  a gate. Before reporting, feed it deliberately bad input and confirm it fails.
- *Board schema:* a `reality_gate` record must carry the harness's **exit code**. An orchestrator
  reading values out of stdout is not evidence and may not be recorded as a pass.

The board line is the anchor: an exit code is a fact you cannot paraphrase, and its absence is
visible on inspection. Note the closing move that actually resolved this story — feeding all four
new assertions bad evidence and confirming **13/13** raise — is the general form and should be named
as the expected practice.

---

## Amendment A8 (proposed, smaller) — separate what a spike REPRODUCED from what it TIMED

**The incident.** My spike reported: *"all 41 signals fired their FIRST cycle within 2s ... so the run
must span startup, not an interval."* One clause was a reproduced control-flow fact. The other was a
timing measurement taken on a synthetic stand-in with **no I/O** — and the real first pass, doing
genuine HTTP and DynamoDB work sequentially, takes 20–90+ seconds. STORY-182's implementer discovered
this the hard way: its first two harness runs captured 37/41 signals before it replaced a fixed sleep
with polling.

The qualitative half was load-bearing and correct. The quantitative half was wrong by more than an
order of magnitude. **They travelled in the same sentence**, which is what let the bad half be
trusted.

**Proposed rung — checklist line.** A spike finding states, per claim, whether it was **reproduced
against the real system** or **measured on a stand-in**, and never mixes the two in one statement. A
stand-in that removes the very I/O the real system spends its time on can validate control flow while
badly mis-measuring cost.

---

## Not proposed as amendments (recorded so they are not re-litigated)

**Citation errors while correcting citations — twice.** I "corrected" `scenario.py:158-160` to
`:156-159` when the story was right (withdrawn in the plan), and my first draft of a wiki update
carried eight wrong line numbers. Both were caught by mechanically re-reading each cited address
against the file before committing.

I considered a `yt_wiki.py` citation lint (parse `` `path:NN` ``, assert the file exists and has ≥NN
lines). **Not proposing it**: it would catch only citations pointing past EOF, not the actual failure
mode here, which is a citation pointing at the *wrong* real line. A check that catches a rare variant
while implying the common one is covered is worse than the existing habit. Re-reading each address
stays a manual discipline until someone finds a rung that genuinely holds it.

**The reviewers' session-limit deaths.** Handled correctly by A5; no change needed.

**Volume of STORY-182 (~1600 lines for 5 points).** The quality reviewer explicitly declined to call
it YAGNI — every module traces to an AC or the story's mandated gate sides. It flagged narrative
duplication as the likely drift point. Noted, not actioned.

---

## Metrics

| | |
| --- | --- |
| Committed / accepted | 8 / 8 |
| Stories / fix rounds | 4 + 1 spike / 1 |
| Rejected / blocked | 0 / 0 |
| Test count | 614 → 666 (+52) |
| Reviewer verdicts | 1 PASS-equivalent, 1 FAIL, 1 FIX_REQUIRED |
| Reality gates run | 6 (187, 183, 184, and 182 × 3), all PASS, all two-or-three-sided |
| Wiki articles rewritten (not re-stamped) | 3 (`demo-engine.md` ×2, `dev-setup-and-dod.md`) |
| Orchestrator errors caught by others | 3 (spike timing, API credentials, `gone_by_pid`) |
