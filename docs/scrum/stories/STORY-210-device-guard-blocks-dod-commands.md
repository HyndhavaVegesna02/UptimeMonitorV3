---
id: STORY-210
title: Harden the DoD gate against the Application Control policy — remaining exe shims + a policy-block diagnostic
type: defect
points: 2
status: ready
filed: 2026-07-31
refined: 2026-08-02
---

## Context

Filed during sprint 66 when a Windows Device Guard / Application Control policy began blocking
`pytest.exe` and `cfn-lint.exe` **mid-sprint** — the gate was green at 11:16 UTC and RED at 16:33
UTC the same day with no code change — taking the full DoD gate red and blocking STORY-197 at AC7.

## What has already been fixed (do not redo it)

The acute failure is **closed**. The PO approved changing the two invocations at the sprint-66
review, and they are in `.scrum/definition-of-done.md` today:

- `pytest` -> `python -m pytest`
- `cfn-lint infra/stack.yaml` -> `python -c "from cfnlint.runner import main; main()" infra/stack.yaml`
  (cfn-lint needed a different answer: the package has no `__main__`, so `python -m cfnlint` does not
  work; a separately blocked `regex` DLL was cleared by reinstalling regex.)

**Verified at sprint-67 planning (2026-08-02, HEAD `86459ea`): the full 8/8 gate is GREEN, exit 0 —
689 passed / 0 skipped, frontend 363 passed.** So this story is no longer "blocks every future
story", and the title has been rewritten to stop claiming that. What remains is the reason the retro
still wanted it first: **the policy widened once, unannounced, and three of the eight commands are
still invoked through shims that the same policy could take tomorrow.**

## The remaining exposure, measured today

| DoD command | Invocation | Exposed? |
| --- | --- | --- |
| `python -m pytest` | module | no |
| `python -c "from importlinter.cli import ..."` | module | no |
| `python -c "from cfnlint.runner import main; ..."` | entry point | no |
| `ruff check .` | `ruff.exe` | **yes** |
| `ruff format --check .` | `ruff.exe` | **yes** |
| `npm test` / `npm run build` / `npm run lint` | `npm.cmd` | **yes, and irreducible locally** |

Measured 2026-08-02: `ruff.exe` is **still allowed** (`ruff --version` -> `ruff 0.15.20`, exit 0), so
the ruff work here is **preventive, not a repair**. `python -m ruff --version` also returns `ruff
0.15.20`, exit 0 — the module form is available and equivalent.

`npm` has no module form. That exposure cannot be closed by an invocation change and must be
**stated** rather than papered over; if npm is blocked, the frontend third of the gate stops running
locally and the answer is a policy exemption or CI, not a clever command. Saying so is part of this
story's deliverable.

## Acceptance Criteria

- [ ] **AC1** — `ruff check .` and `ruff format --check .` become `python -m ruff check .` and
      `python -m ruff format --check .` in `.scrum/definition-of-done.md`, with a dated note giving
      the reason, mirroring the two existing precedents in that file (2026-07-12 `lint-imports`,
      2026-07-31 `pytest`/`cfn-lint`). **This changes the DoD and is a PO decision** — it is called
      out for approval in the sprint plan and must not be taken unilaterally.
- [ ] **AC2** — Every other statement of those commands is updated in the SAME commit: `CLAUDE.md`
      (Key commands table and the DoD-gate section) and `docs/scrum/wiki/dev-setup-and-dod.md`.
      Grep evidence before and after. (Sprint 66's review found `CLAUDE.md` still instructing the
      blocked shims after the DoD changed — the identical miss, one story earlier.)
- [ ] **AC3** — `yt_gate.py` detects a policy-blocked command and reports it **distinctly from a code
      failure**, naming it as an environment block and printing the 2026-07-06 proof protocol
      (empty diff since the sprint cut + passes in isolation) that the orchestrator must satisfy
      before discounting it. Detection keys on the observed signatures — exit code `4551` and/or
      `blocked by your organization` / `Application Control policy has blocked` in the output.
- [ ] **AC4** — **The classification must never downgrade a red.** A policy-blocked command still
      exits nonzero, still records `exit_code` faithfully, and still fails the gate. AC3 adds a
      *label*, not an escape hatch. A test asserts the gate's overall exit is still nonzero when a
      command is policy-blocked. (This AC exists because A12's motivating incident was precisely a
      guard whose message invited an action its check could not justify; "environmental" is exactly
      the word that could become an excuse to wave a red through.)
- [ ] **AC5** — Shown RED **and** shown not-firing, two-sided: a stand-in command reproducing the
      policy signature is classified as a policy block, **and** a genuinely failing command (a real
      test failure) is NOT classified as one. A detector that labels everything environmental is
      worse than none.
- [ ] **AC6** — The skill stays **project-generic** (PO directive 2026-07-13): no project names,
      paths, or command names in `yt_gate.py`. The signatures are platform-level, not project-level,
      which is why they belong in the runner at all.
- [ ] **AC7** — The irreducible `npm` exposure is recorded honestly in the DoD note and the story
      report: no module form exists, so a block there is a policy/CI problem. The story may not claim
      the gate is fully hardened.
- [ ] **AC8** — Full 8/8 DoD gate green at the new invocations, and `yt_selftest` green.

## Rung note

AC3/AC4 land at the **script** rung inside an existing mechanism (`yt_gate.py`), which the
2026-08-01 **A14** amendment explicitly exempts from the mid-sprint tooling freeze. It also
mechanizes the first step of the 2026-07-06 agreement, which until now has been prose applied from
memory — and was applied correctly in sprint 66 only because the orchestrator happened to recognize
the signature.

## Open Questions

None. Estimate confirmed at 2.

## History

- 2026-07-31: filed by STORY-197, which it blocked at AC7.
- 2026-08-02: refined to `ready` at sprint-67 planning and **substantially rescoped**. The acute
  failure was fixed during sprint 66 (PO-approved invocation changes), so the filing's framing —
  "blocks every future story, fix before the next sprint" — is no longer true and the title said so
  misleadingly; both corrected. Re-measured the remaining exposure: `ruff.exe` is still permitted, so
  AC1/AC2 are preventive; `python -m ruff` confirmed working; `yt_gate.py` confirmed to contain **no**
  policy-block detection today (grep for `4551` / `Device Guard` / `Application Control` returns
  nothing across its 389 lines), so AC3-AC5 are genuinely new work.
