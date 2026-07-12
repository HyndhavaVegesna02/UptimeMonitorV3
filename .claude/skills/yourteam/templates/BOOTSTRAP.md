# Bootstrap payload (yourteam_version: 2.0.0)

What inception generates into a project, from this directory (ceremonies.md §1 step 6):

| Source | Destination | Rule |
|---|---|---|
| `agents/yt-*.md` | `.claude/agents/` | Copy; confirm model tiers with the PO (defaults: Sonnet implementer, Opus reviewers + verifier, Haiku scout) |
| `hooks/yt_git_guard.py` | `.claude/hooks/` | Copy |
| `hooks/settings-fragment.json` | `.claude/settings.json` | **MERGE** the hooks block — never overwrite; PO confirms |
| `checklists/*.md` | `.scrum/checklists/` | Copy; "Project conventions" sections start empty and grow via retro routing |
| `backlog.yaml`, `sprint-current.yaml`, `velocity.json`, `definition-of-done.md`, `working-agreements.md`, `story.md` | `.scrum/` + story scaffolding | As in v1 inception |

Never copied: `scripts/` and `references/` — they run from the skill directory and read project
state at runtime, so fixes propagate to every project at once.

Every generated file carries a `yourteam_version` marker. At standup, if the skill's version
differs from the project's generated files, offer the PO a re-sync diff (show what changed,
apply on approval). This project (uptime_monitor_v3) is the reference instantiation.
