# Wiki Protocol

The wiki (`docs/scrum/wiki/`) is the project's living knowledge base: architecture decisions and their reasons, domain rules, gotchas ("library X breaks if Y"), module guides. It exists so knowledge learned in one sprint doesn't die with the session.

**The invariant everything below enforces:** the wiki can be incomplete, but never trusted-and-wrong. Every claim is provably current, visibly stale, or absent. There is no fourth state.

**The ground rule:** the wiki is a map, never the territory. Code is always the source of truth. Wiki claims guide navigation; load-bearing decisions still require confirming against the referenced file. A wrong wiki is worse than no wiki — missing docs make you investigate, wrong docs make you stop investigating.

## Article Format

```markdown
---
title: Auth flow
code_refs: [src/auth/, src/middleware/session.py]
verified_sha: a1b2c3d
verified_sprint: sprint-04
status: verified          # verified | stale | archived
---

## Facts (verified against code)
- Sessions use JWT, issued in `src/auth/token.py:42`
- Tokens expire after 24h (`src/auth/config.py:7`)

## Inference (synthesis, not verified)
- JWT was likely chosen for stateless horizontal scaling.

## History
- sprint-03: created (STORY-008)
- sprint-04: re-verified after session refactor (STORY-015)
```

Rules:
- **Facts cite addresses** (`file:line` or at least file). A claim without an address goes under Inference. This separation is what stops hallucinated synthesis from laundering into established fact over compile cycles.
- `code_refs` lists the paths this article *describes* — the blast-radius hooks.
- `verified_sha` is the commit at which a human-or-agent last confirmed the Facts against actual code.

## Staleness: Git Arithmetic, Not Judgment

An article is stale when its code has moved under it:

```bash
git diff --name-only <verified_sha>..HEAD -- <each code_ref>
```

Any output → set `status: stale`. This check is mechanical on purpose — no LLM judgment, so no blind spots. A deleted file is a diff hit like any other change, so deletions auto-flag dependents.

**v2: the check is a script** — `python .claude/skills/yourteam/scripts/yt_wiki.py` runs the
sweep over all articles plus two lints: Facts-coverage (every file a Fact cites is inside the
article's `code_refs`, else that Fact can rot invisibly) and internal links. `sweep --update`
rewrites flagged articles to `status: stale`. Exit 0 is the compile-pass precondition.

Run the check:
- At every standup (over all `verified` articles — it's cheap)
- Before building any subagent brief that would consume an article

## Quarantine Rule

`stale` articles are readable but demoted: **their claims never enter a subagent brief.** Briefs include `verified` content only. If everything relevant is stale, the subagent gets no wiki content and explores the code manually — the worst case degrades to "no wiki," never to confidently wrong.

## Forward Blast Radius (code → knowledge), at the DoD Gate

When a story completes:
1. `git diff --name-only <story-start>..<story-end>` → changed paths
2. Match against every article's `code_refs`
3. Every hit is in the blast radius. For each: **update** the article (and bump `verified_sha` to current) or explicitly **re-verify** ("read the code, Facts still accurate, bump SHA").
4. Unresolved blast radius = story does not pass the DoD gate. Staleness cannot accumulate silently; it is mechanically blocked, same as a failing test.

## Reverse Blast Radius (knowledge → code), at Dispatch

Before dispatching an implementer: collect `verified` articles whose `code_refs` overlap the story's expected files. Their Facts sections go into the brief. This is also the momentum signal at planning ("story touches files we just documented") and the risk signal at refinement (many articles referencing a path = load-bearing code = bump the estimate).

## Sprint-End Compile Pass (blocks review)

Before the review may be called:
1. Fold the sprint's raw material — story outcomes, review-worthy discoveries, gotchas hit, decisions made — into articles: update existing, create new ones for concepts that earned them.
2. Rehabilitate or archive remaining `stale` articles touched this sprint.
3. **Link lint** (mechanical): grep internal wiki links, verify each target exists. Broken → repoint to the archive tombstone or prune.
4. Report drift in the retro: articles stale ≥3 sprints get a decision — recompile or archive. An honest gap beats a decaying claim.

Per-story stale-flagging already happened in real time (the SHA check), so batching the *writing* to sprint-end delays nothing safety-critical.

## Archiving and Tombstones

Deletion adds knowledge instead of erasing it.

- Code deleted → dependent articles move to `wiki/archive/` with a tombstone header:

```markdown
---
status: archived
archived_sprint: sprint-09
archived_reason: "Polling sync removed in STORY-023 — replaced by websocket push; polling caused thundering-herd load"
---
```

- A story that deletes code **must record why** in its story file/commit message — that reason feeds the tombstone. This is what stops a future sprint from re-introducing something deliberately killed.
- Archived articles are never link-lint targets to fix — links *to* archive are valid history.
- `docs/scrum/sprints/` and `stories/` history is exempt from all of this: append-only records of the past are allowed to reference dead code, like old meeting notes. Only `wiki/` must stay current.
