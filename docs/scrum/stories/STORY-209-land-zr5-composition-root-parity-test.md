---
id: STORY-209
title: Land ZR-5's guard — a composition-root parity test for CONFIG_DIR resolution (code-level half only)
type: chore
points: 2
status: draft
filed: 2026-07-31
refined: 2026-08-05
sprint: 69
---

> **REFINED at sprint-69 planning (2026-08-05).** AC lifted from `docs/scrum/wiki/zone-rules.md`
> ZR-5's Coverage verdict and re-verified against HEAD. PROPOSAL until the PO approves the sprint.
> **Estimate confirmed at 2.**

## Read the scope limit before reading the AC

**This guard cannot cover the failure that actually caused the sprint-64 incident.** The loop and
the API are separate OS processes, each reading its own environment; setting `CONFIG_DIR` in one
does not propagate to the other, and no single-process test sees across a process boundary. That
half is **UNGUARDABLE** by a unit test and stays runbook discipline — operationally it is covered
only by `tools/demo_loop_gate/harness.py` setting the env explicitly on BOTH child processes.

What the guard CAN do is catch the regression shape *"one root starts resolving config
independently of the other"*, which is real. It must not be described as more.

## Re-verification at HEAD (2026-08-05, planning)

Both roots agree today, through one function:

- `backend/src/composition/run.py:182-184` — `settings = load_settings()`, then
  `config = load_config(settings.config_dir)`.
- `backend/src/composition/app.py:97` — `settings = load_settings()`; `:137` —
  `cfg_dir = config_dir or settings.config_dir`.
- `backend/src/composition/settings.py:46` — `config_dir=os.environ.get(CONFIG_DIR_VAR, "config/apps")`,
  with `CONFIG_DIR_VAR = "CONFIG_DIR"` at `:32`.

`grep -rn "CONFIG_DIR" backend/src/` returns hits in **`settings.py` only** — neither composition
root reads the variable directly today. The `tools/demo_loop_gate` modules import `CONFIG_DIR_VAR`
from `src` rather than re-declaring it (ZR-3-compliant). The tree is clean, so AC4 is the only
possible red.

Two notes for the implementer, both from plan verification:

- `app.py`'s `create_app(config_dir=...)` parameter legitimately overrides the setting for tests.
  The guard forbids reading the **env var** in the two roots — not the parameter.
- **Neither `app.py` nor `run.py` imports `os` at module level**, so the AC4/AC5 mutations need an
  `import os` added alongside. The AST guard still fires on the string literal, so the proof holds —
  but do not read the resulting `NameError` (if you forget the import) as the guard failing.
  Verified: no test monkeypatches `load_settings`, and `test_asgi.py:18` passes `config_dir=`
  explicitly, which wins at `app.py:137` either way — so the mutation genuinely leaves runtime
  behaviour identical, which is exactly why prose never caught this shape.

## Acceptance Criteria

- [ ] **AC1 — resolution parity.** A test patches `CONFIG_DIR` to an arbitrary value and asserts
      `load_settings().config_dir` resolves to exactly it; with `CONFIG_DIR` unset it asserts the
      default `"config/apps"`. Both roots call this one function, so this pins the shared mechanism.
- [ ] **AC2 — neither root reads the env var itself.** A source-level (AST) assertion over
      `composition/run.py::main` and `composition/app.py::create_app`: neither references the
      `CONFIG_DIR` env name — as a literal, via `os.environ[...]`/`os.environ.get(...)`, or via
      `CONFIG_DIR_VAR` — and both reach config through `load_settings()`. The named-parameter
      override on `create_app` is explicitly permitted and the test says so.
- [ ] **AC3 — BOTH limits are in the guard's own docstring.** (a) The operational two-process half
      is UNGUARDABLE by this test; `tools/demo_loop_gate/harness.py` is the only thing covering it,
      and it is procedural. Anyone reading a green run must not read it as "the sprint-64 incident
      cannot recur". (b) **The code-level residue, added at plan verification:** ZR-5 forbids two
      things — *"neither may hardcode a different default **or** read a different env var than the
      other"* (`zone-rules.md:437-438`) — and AC2 catches only the second. A root that hardcodes
      `load_config("config/apps")` passes AC2 entirely, including its `load_settings()` clause,
      because both roots call `load_settings()` for other fields regardless. That half is undetected
      and the docstring says so.
- [ ] **AC4 — shown RED by mutation (A9).** Change `composition/app.py::create_app` to read
      `os.environ.get("CONFIG_DIR", "config/apps")` directly instead of using `settings.config_dir`
      — a mutation that leaves behaviour identical today, which is exactly why prose never caught
      it. The test fails naming that root; revert; green; `git diff` empty. Recorded verbatim in the
      board's `reality_gate` block.
- [ ] **AC5 — a second mutation on the other root.** The same change applied to
      `composition/run.py::main` also fails, naming `run.py`. A guard that only watches one of the
      two roots would be the exact asymmetry ZR-5 is about. Reverted; `git diff` empty.
- [ ] **AC6 — runs inside the existing gate.** A `backend/tests/` test collected by the existing
      `python -m pytest`. No ninth DoD command. It must not import
      `tools/demo_loop_gate` (nothing under `backend/` may depend on `tools/`).
- [ ] **AC7 — the catalogue row flips, keeps its limit, and stays parseable.** ZR-5's adjudication
      row moves from `GUARDABLE-DEFERRED (STORY-209)` to `ENFORCED-BY` with the test path as a
      backtick code span in the **Verdict** cell — **the "(code-level half only)" parenthetical goes
      OUTSIDE the code span**, or it becomes part of the path and STORY-216 false-reds on it. The
      operational half stays stated as `UNGUARDABLE` in the same cell; STORY-216 AC1 explicitly
      permits a cell carrying both verdicts and names ZR-5 as the case (the legend's "exactly one
      verdict" line, `zone-rules.md:801`, is corrected in this same commit — ZR-5 already breaks it
      at `:812` today). Detail records the AC4/AC5 mutations and AC3(b)'s residue. `verified_sha`
      bumped in the same commit (A18 / C3).

## Not in scope

The operational half (above — it is not guardable here, by construction). Changing how either root
resolves config. `tools/demo_loop_gate/harness.py`'s env-setting discipline, which already works.
