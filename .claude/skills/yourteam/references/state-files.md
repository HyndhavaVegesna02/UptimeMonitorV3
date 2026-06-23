# State File Schemas

Read before creating or editing any `.scrum/` file. Templates with these shapes live in `templates/`.

## backlog.yaml

```yaml
next_story_id: 18
stories:
  - id: STORY-012
    title: Daily habit check-off
    file: docs/scrum/stories/STORY-012-daily-checkoff.md
    status: ready            # draft | ready | done | rejected
    points: 3                # 1,2,3,5,8 — an 8 may not enter a sprint
    priority: 2              # PO-ordered, 1 = highest
    type: feature            # feature | defect | chore
    sprint: null             # set when pulled into a sprint
  - id: STORY-013
    title: Reminders
    file: docs/scrum/stories/STORY-013-reminders.md
    status: draft
    points: null
    priority: 5
    type: feature
    sprint: null
```

Rules: stories are never removed (rejected/done are history); `done` is set only by an accept verdict at review; `ready` requires the Definition of Ready.

## sprint-current.yaml

```yaml
sprint: 4
goal: "Habits can be checked off daily and streaks are visible"
branch: sprint-4
start_tag: sprint-4-start
started: 2026-06-10
status: active               # active | review | closed | aborted
stories:
  - id: STORY-012
    points: 3
    board: done              # todo | in-progress | blocked | review | done
    pipeline: full           # light (1-2 pts) | full (3+)
    blocked_question: null
    attempts: 1              # effort cap: auto-block at 3x estimate-proportional attempts
    paused_at_commit: null   # set by hotfix protocol
    dod_evidence:
      - command: "npm test"
        exit_code: 0
        output_tail: "Tests: 24 passed, 24 total"
        commit: 9f8e7d6
        at: 2026-06-10T14:32:00Z
      - command: "npx eslint ."
        exit_code: 0
        output_tail: ""
        commit: 9f8e7d6
        at: 2026-06-10T14:33:00Z
    blast_radius_resolved: true   # forward blast radius cleared at DoD
  - id: STORY-014
    points: 2
    board: blocked
    pipeline: light
    blocked_question: "AC says 'send a notification' — email or SMS? Both are supported."
    attempts: 1
    dod_evidence: []
    blast_radius_resolved: false
hotfixes: []                 # {branch, reason, merged_sha, caused_by_story}
interrupts: []               # PO mid-sprint requests parked here: {at, text, became_story}
```

`dod_evidence` is the mechanical record: a story may be `done` only when every DoD command has an entry with exit_code 0 at the story's final commit, and `blast_radius_resolved: true`.

## velocity.json

```json
{
  "sprints": [
    {"sprint": 1, "committed": 5, "accepted": 5},
    {"sprint": 2, "committed": 8, "accepted": 6},
    {"sprint": 3, "committed": 7, "accepted": 7}
  ]
}
```

Capacity at planning = mean of last 3 `accepted`. Only PO-accepted points count.

## session.lock

```yaml
session_id: <random id generated at standup>
acquired: 2026-06-10T09:00:00Z
```

Write at standup; honor an existing live lock by going read-only. Delete on clean session end; a lock older than 24h may be assumed dead and replaced (note it to the PO).

## definition-of-done.md

Human-readable list where every item is a command + expected exit code, plus the standing rules. See `templates/definition-of-done.md`. The gate runner executes each command literally; prose items ("code reviewed") are allowed only when they map to a recorded pipeline step.

## working-agreements.md

Append-only amendments with date + motivating incident. See `templates/working-agreements.md`. Standup loads this file; agreements bind all subagent briefs.

## Story file (docs/scrum/stories/STORY-NNN-slug.md)

See `templates/story.md`. The file never moves; status lives in backlog.yaml. PO feedback from rejections and blocker answers are appended under History — the story accumulates its journey.
