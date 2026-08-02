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

**`npm`'s position, stated as measured rather than as assumed.** An earlier revision of this story
and of the sprint plan asserted "npm has no module form; the exposure is irreducible". That was an
**inference, not a measurement, and it is wrong as stated.** Measured 2026-08-02:

```
node "C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js" --version   ->  11.6.2, exit 0
npm --version                                                             ->  11.6.2, exit 0
```

`npm.cmd` is a batch shim, and running `npm-cli.js` under `node.exe` bypasses it — the direct
analogue of `python -m ruff`. What is **unverified** is whether the Application Control policy would
block the `.cmd` while permitting `node.exe`; nothing has tested that, and it cannot be tested until
the policy actually blocks something. So the honest position is: a shim-free form **exists**, its
value against this policy is **unknown**, and adopting it is a separate DoD decision that is not part
of this story.

## Acceptance Criteria

- [x] **AC1** — `ruff check .` and `ruff format --check .` become `python -m ruff check .` and
      `python -m ruff format --check .` in `.scrum/definition-of-done.md`, with a dated note giving
      the reason, mirroring the two existing precedents in that file (2026-07-12 `lint-imports`,
      2026-07-31 `pytest`/`cfn-lint`). **This changes the DoD and is a PO decision** — it is called
      out for approval in the sprint plan and must not be taken unilaterally.
- [x] **AC2** — Every **live instruction** stating those commands is updated in the SAME commit, with
      grep evidence before and after. The lines are **enumerated**, because "update every statement"
      is too blunt an instruction here and would corrupt the historical record:

      | File | Lines | Action |
      | --- | --- | --- |
      | `.scrum/definition-of-done.md` | 58, 59 | change (AC1) |
      | `CLAUDE.md` | 168, 169, 191 | change |
      | `docs/scrum/wiki/dev-setup-and-dod.md` | 65, 66 | change |
      | `docs/scrum/wiki/dev-setup-and-dod.md` | 80 | prose — judgement call |
      | `docs/scrum/wiki/dev-setup-and-dod.md` | **202-203** | **DO NOT TOUCH** |

      `dev-setup-and-dod.md:202-203` is a **dated sprint-22 history note** about `[tool.ruff]
      exclude`. It records what was true then. Rewriting it would falsify the record — the same class
      of error as re-stamping a stale wiki article as current.

      Also out of scope: `.agents/skills/yourteam/scripts/yt_gate.py`. That copy differs from the
      `.claude/` one but `.agents/` is gitignored (`.gitignore:30`) and untracked. Noted here so a
      reviewer does not file it as a miss.

      (Sprint 66's review found `CLAUDE.md` still instructing the blocked shims after the DoD
      changed — the identical miss, one story earlier.)
- [x] **AC3** — `yt_gate.py` detects a policy-blocked command and reports it **distinctly from a code
      failure**, naming it as an environment block and printing the 2026-07-06 proof protocol
      (empty diff since the sprint cut + passes in isolation) that the orchestrator must satisfy
      before discounting it. Detection keys on the observed signatures — exit code `4551` and/or
      `blocked by your organization` / `Application Control policy has blocked` in the output.
- [x] **AC4** — **The classification must never downgrade a red.** A policy-blocked command still
      exits nonzero, still records `exit_code` faithfully, and still fails the gate. AC3 adds a
      *label*, not an escape hatch. A test asserts the gate's overall exit is still nonzero when a
      command is policy-blocked. (This AC exists because A12's motivating incident was precisely a
      guard whose message invited an action its check could not justify; "environmental" is exactly
      the word that could become an excuse to wave a red through.)
- [x] **AC5** — Shown RED **and** shown not-firing, two-sided: a stand-in command reproducing the
      policy signature is classified as a policy block, **and** a genuinely failing command (a real
      test failure) is NOT classified as one. A detector that labels everything environmental is
      worse than none.
- [x] **AC6** — The skill stays **project-generic** (PO directive 2026-07-13): no project names,
      paths, or command names in `yt_gate.py`. The signatures are platform-level, not project-level,
      which is why they belong in the runner at all.
- [x] **AC7** — The `npm` position is recorded in the DoD note and the story report **as measured,
      not as inferred**: no `-m` form exists, but `node <npm_root>/bin/npm-cli.js` is a shim-free
      analogue (verified `11.6.2`, exit 0, 2026-08-02), and its behaviour under the policy is
      **UNVERIFIED**. Adopting it is a separate PO decision, out of scope here. The story may not
      claim the gate is fully hardened, and may not write "no module form exists" into the DoD as a
      permanent fact — that phrasing was already caught once as an inference presented as a
      measurement.
- [x] **AC8** — Full 8/8 DoD gate green at the new invocations, and `yt_selftest` green.

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
