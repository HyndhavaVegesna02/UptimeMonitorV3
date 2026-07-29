# Sprint 62 Retro — process, not product

**Sprint outcome:** 3/3 stories Done, 9/9 points accepted, kept unmerged. Full gate 8/8 on
final HEAD `2b0bf86`. This retro looks only at *how* that happened.

## What the numbers say

| Signal | Sprint 62 |
|---|---|
| Stories committed / Done / accepted | 3 / 3 / 3 |
| Points committed / accepted | 9 / 9 |
| Blocked stories | 0 |
| Reviewer rejections | 2 of 2 reviewed stories came back FIX_REQUIRED on quality (7 majors total, all fixed) |
| Spec-review verdicts | 2/2 PASS, no gaps, no scope additions |
| Estimate changes | STORY-146 3 → 5 and STORY-148 5 → (3 + 4, split) — **both caught pre-lock** by the verifier passes, not discovered mid-sprint |
| Hotfixes | 0 |
| Agent crashes | 2 (one during STORY-146's rework, one mid-STORY-149) |
| Wiki drift at close | sweep / facts / links / integrity **CLEAN**; 0 articles stale, 0 stale ≥3 sprints |
| Tooling defects filed | 4 (STORY-173, -178, -179, -180) |

Two plan-verifier passes ran pre-lock, both verdict GAPS. Pass 2 was briefed to attack pass
1's *fixes* and found three fix-introduced errors plus one blocker both passes and I had
missed. **That second pass paid for itself** — decision D-A came out of it, and without D-A
STORY-149's reality gate would have false-passed on the last day of the sprint.

## The one thing this sprint actually taught

**A wiki Fact that agrees with the code can still be wrong, and the staleness machinery is
structurally blind to it.**

`core-pipeline-and-availability.md` stated that anti-flap's `DEGRADED` branch is "always
`degraded`, regardless of length — there is only one failing-adjacent bucket for this health,
so no length comparison applies." That sentence *was* STORY-149's defect. It survived since
sprint-8 — through every staleness sweep, every Facts-coverage lint, every compile pass —
because it faithfully paraphrased `pipeline.py`'s own docstring. The article and the code
agreed. Git arithmetic detects *divergence*; it cannot detect *shared error*.

The premise ("only one bucket") was true. The conclusion ("so no length check") never
followed from it. A Fact that restates the implementation's own words adds no verification
value — it launders the code's self-description into "verified knowledge" and gives a future
reader a second source that isn't one.

## Where verification caught itself (three times — worth keeping visible)

1. **STORY-146's reality gate false-passed twice.** First run: "IDENTICAL" on two **empty**
   dumps (`md5 d41d8cd9…`), because DynamoDB Local partitions databases by access key without
   `-sharedDb` and the dump script used a different key than the code under test. Second:
   filtering on uppercase `PK/SK` where the schema uses lowercase. Fixed by making the dump
   script *refuse* to emit an empty dump (exit 2).
2. **One of STORY-148's 19 checks was a tautology.** It asserted an empty API token is
   rejected; `api_token=""` yields the header value `"Api-Token "`, and httpx/h11 refuses to
   transmit a header value with a trailing space. The request never left the client.
3. **STORY-149's gate was run at the pre-fix commit on purpose** — 7/12, failing on exactly
   the five checks the fix owns. That is the only reason its 12/12 means anything.

The common thread: **a PASS whose failure mode is indistinguishable from "nothing happened"
is not evidence.** Two of the three were caught only because I went looking; nothing in the
process required me to.

## Proposed amendments (enforcement-ladder routed)

### A1 — A reality gate must be shown able to fail

**Rule.** No reality gate may be reported PASS without a recorded answer to "how could this
have failed?", in one of two forms:
- **Defect / fix stories:** run the *same, unmodified* gate at the pre-fix commit (worktree)
  and record both scores. A gate that passes at the pre-fix commit is not a gate.
- **All other stories:** name, per assertion that could pass one-sidedly, the second side
  that was asserted — or state explicitly that the assertion is one-sided and why that is
  acceptable.

The board's `reality_gate` record carries the answer in a required field
(`discrimination_proof` for the first form, `two_sided_note` for the second). Its absence is
grep-visible on the board.

**Rung: prose (working agreement), with a state-file field as the visible artifact.** A
mechanical rung was considered and rejected: a reality gate is bespoke per story, so no
script can judge whether a given assertion could have failed. The required field is the
lowest rung that actually holds — it makes the omission *visible* even though it cannot make
it *impossible*.

**Motivating incidents:** all three above, this sprint. I wrote both fields voluntarily; the
sprint before, nothing would have asked for them.

### A2 — A behavioural wiki Fact cites the test that pins it, not only the implementation

**Rule.** A Fact asserting *behaviour* (a branch, a threshold, a decision ladder, an error
condition) cites the **test** that pins it alongside the implementation symbol. A Fact whose
only support is a paraphrase of the code's own docstring is marked as such or dropped —
it is a restatement, not a verification.

**Rung: role checklist** — `.scrum/checklists/implementer.md`, "Wiki discipline" section,
where the existing three wiki rules already live and where the blast-radius pass reads them.
Not prose: this is a per-article, per-story action an implementer takes, exactly the shape of
the items already on that checklist. A mechanical rung is partly available and *not* proposed
yet — `yt_wiki.py`'s Facts lint could require that an article whose `code_refs` include test
files cites at least one of them, but that is a weak proxy (an article can cite one test and
paraphrase ten docstrings), so the checklist rung goes first and the lint waits for evidence
that the checklist isn't enough.

**Motivating incident:** the anti-flap Fact above, wrong and "verified" for 54 sprints.

## Already routed to code — not re-proposed as prose

- **STORY-178 — `yt_gate.py`, three defects.** (a) `--only` exits 0 when nothing matches: a
  false green on the DoD gate itself. (b) `--only` is a repeatable *substring* flag, not CSV —
  a comma-joined value silently matches nothing, which is (a)'s trigger. (c) ANSI/C0 bytes in
  `output_tail` make the emitted fragment **invalid YAML**. (c) recurred a **third** time
  this sprint and is the sharpest: the skill instructs merging the fragment *verbatim*, and
  verbatim has been impossible three sprints running. Whatever fixes it must fix the
  instruction or the emitter, not the merger.
- **STORY-179 — `dynamo_local` fixture, two defects.** The ephemeral host port it picks is
  mapped by Docker but not routable from the Windows host, so every DynamoDB-gated run this
  sprint needed a manual fixed-port container and an `env_note` on every gate record.
- **STORY-173 — leaked containers** from earlier fixture runs.
- **STORY-180 — STORY-148's 8 non-blocking review minors**, deliberately not absorbed
  in-story. Two of them (an unevicted token cache, a hardcoded 2h window) only start to
  matter once STORY-176 makes the engine long-running, so they may belong there.

## Observations not (yet) worth a rule

- **Crash recovery worked, twice, unprompted.** STORY-149's implementer died mid-story on an
  API session limit; the commit-per-green-step cadence meant the only loss was the wiki pass.
  Nothing needs changing — this is the mechanism doing its job. Worth noting that neither
  crash was detected by the ~30-minute-silence rule; both surfaced as task notifications.
- **CLAUDE.md drift is unenforced.** It documented no `tools/` package and claimed
  import-linter enforces "the five contracts" while the runner prints `Contracts: 8 kept` —
  contracts 5–7 landed without the file being touched. The DoD standing rule ("a story that
  changes architecture updates CLAUDE.md") is prose with nothing beneath it. Corrected by
  hand this sprint. **Not proposed as an amendment yet** because the honest fix is a
  project-specific script, and I would rather see it recur once more with the rule in place
  than build a checker on one data point.
- **`code_refs` amplifiers.** `yt_wiki.py` reports `run.py` in 4 articles and
  `pyproject.toml` in 5 — a touch on either quarantines all of them. It has reported this for
  several sprints without anyone acting. Either narrow the refs or stop printing the note.
- **Test files as `code_refs` cut both ways.** They keep test-pinned Facts staleness-checked
  (the 2026-06-25 rule, and A2 above leans on it) but they also make routine test edits
  quarantine articles whose claims did not move. Three of this sprint's five re-verifications
  were exactly that shape.

## PO decision (2026-07-29): both approved, landed

- **A1 approved** → landed in `.scrum/working-agreements.md` as the 2026-07-29 entry, with all
  three motivating incidents and the explicit note that the mechanical rung was considered and
  rejected. Binds every future session; the required `discrimination_proof` /
  `two_sided_note` field is the visible artifact on each board `reality_gate` record.
- **A2 approved** (checklist rung only — the `yt_wiki.py` lint variant stays held back) →
  landed in `.scrum/checklists/implementer.md`, "Wiki discipline", directly beneath the
  existing `code_refs`-coverage item, so it is read on every blast-radius pass.

Sprint 62 is closed. Sprint 63 opens with STORY-176, branching from `sprint-62` (nothing was
merged to main).
