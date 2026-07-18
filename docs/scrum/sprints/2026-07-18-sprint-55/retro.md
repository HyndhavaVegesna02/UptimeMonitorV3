# Sprint 55 Retro — 2026-07-18

1. **Three session-limit/API crashes this sprint** (STORY-099-era pattern continued):
   one killed a dispatch pre-write, one mid-fix (orchestrator landed the verified tail —
   trivial-tails rule, worked well), one lost the Playwright MCP for the session. The
   commit-per-green-step cadence + board-commit-before-dispatch made every recovery
   mechanical. The ui-sweep scripted-Chromium harness proved a full-fidelity fallback for
   live gates — codify it: **A1 (sprint-55): when browser-MCP tooling is unavailable,
   reality gates run via tools/ui-sweep's Playwright with the same evidence bar** (rung:
   prose here; the harness already exists at the script rung).
2. **Design-authority corrections at the reality gate work.** The dark-first precedence
   fix was caught live (headless reported system-light), corrected same-story, and
   re-verified in a fresh context. Keep the gate empowered to overrule implementation
   choices that satisfy tests but miss design intent.
3. **ui-ux-pro-max integration deepened per PO instruction**: domain searches now feed
   story briefs (STORY-104 carried its navigation/a11y rules verbatim; STORY-105 gets a
   chart-domain pass). **A2 (sprint-55): every rewrite story brief includes the relevant
   skill domain-search rules** (rung: brief-writing practice, recorded here).
4. Spec review caught a DoD-process gap (deletion reason must live in the story file) —
   the mechanical floor of checklists holding up exactly as designed.
