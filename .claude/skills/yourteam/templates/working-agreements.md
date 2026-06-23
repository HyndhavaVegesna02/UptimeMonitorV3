# Working Agreements
# Append-only. Each entry: date, the agreement, and the incident that motivated it.
# These bind every session and every subagent brief.
# Team-proposed amendments enter only via retro with PO approval.
# PO-stated rules (coding style, conventions, process preferences) are appended
# IMMEDIATELY whenever the PO states them — the PO never waits for a ceremony.
# PO-stated rules outrank observed codebase patterns wherever they conflict.

## Defaults (active from inception)
- 2026-01-01 — Execution pipeline: stories of 1-2 points use implementer + DoD gate;
  3+ points use implementer + spec reviewer + quality reviewer + DoD gate.
  The DoD gate is never skipped at any size. (Default)
- 2026-01-01 — Effort cap: a story exceeding 3x its estimate in attempts is
  auto-Blocked with a summary of what was tried. (Default)
- 2026-01-01 — An 8-point story must be split during refinement; it may never
  enter a sprint. (Default)
- 2026-01-01 — Tooling (MCP servers, CLIs) may only change at sprint planning or
  retro; mid-sprint the environment is frozen like scope. (Default)
- 2026-01-01 — One active session: honor .scrum/session.lock; a second session
  runs read-only. (Default)

## Amendments
<!-- - YYYY-MM-DD — <agreement> (Motivated by: <incident, sprint, story>) -->
