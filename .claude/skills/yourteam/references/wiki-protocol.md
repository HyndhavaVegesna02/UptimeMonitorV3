# Wiki Protocol

The wiki (`docs/scrum/wiki/`) is the project's living knowledge base: architecture decisions and their reasons, domain rules, gotchas ("library X breaks if Y"), module guides. It exists so knowledge learned in one sprint doesn't die with the session.

**The invariant everything below enforces:** the wiki can be incomplete, but never trusted-and-wrong. Every claim is provably current, visibly stale, or absent. There is no fourth state.

**The ground rule:** the wiki is a map, never the territory. Code is always the source of truth. Wiki claims guide navigation; load-bearing decisions still require confirming against the referenced file. A wrong wiki is worse than no wiki — missing docs make you investigate, wrong docs make you stop investigating.

**Who it is for.** A human reading a stale doc discounts it automatically. A cold subagent cannot — it takes its brief as given. That is the entire reason for the three-state invariant, and it is why the machinery below is worth paying for on the articles a brief actually consumes, and nowhere else.

## Route Knowledge Before You Write It

The enforcement ladder routes *rules* to the lowest rung that can hold them. Knowledge gets the same treatment, and for the same reason: **a Fact that cites `file:line` and can go stale is a test that hasn't been written yet.**

Ask, in order, at the compile pass and any time you are about to write an article:

| Ask | If yes → | Why it costs nothing there |
| --- | --- | --- |
| 1. Can this be a test, lint or gate command? | **Write the check.** Not the wiki. | It fails instead of rotting. A guard cannot be silently wrong. |
| 2. Is it load-bearing every session? | **CLAUDE.md.** | Always in context, free to keep current, no staleness tracking possible or needed. |
| 3. Is it a *reason* — why a decision was made, why code was killed? | **`tier: reference` article.** | The past does not rot. Append-only, cites no live line. |
| 4. Otherwise (a navigation map of a subsystem) | **`tier: map` article.** | The only tier that carries staleness — and the only one that pays for it. |

Rows 1–3 are unfalsifiable by construction, which is a *stronger* guarantee than a verification stamp, not a weaker one. Only row 4 needs git arithmetic watching it, so keep row 4 small: every article there is recurring cost.

Routing is a compile-pass decision, so it is recorded like one — a story that converts a Fact into a guard says so, and the article keeps a link to the test that replaced it.

## Article Format

```markdown
---
title: Auth flow
tier: map                 # map | reference   (absent = map)
code_refs: [src/auth/, src/middleware/session.py]
verified_sprint: sprint-04
status: verified          # verified | stale | archived   (map only)
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
- **There is no `verified_sha`.** The verification baseline is derived from git; see below.

A `tier: reference` article carries **no `code_refs` and no `## Facts` section** — mechanically checked by `yt_wiki.py integrity`. That is what makes its exemption from staleness honest rather than an escape hatch: it asserts nothing about live code, so it has nothing that can rot. The moment a reference article wants to cite code, it is a map article and must be one.

## Staleness: Git Arithmetic, Not Judgment

An article is stale when its code has moved under it. The baseline is **the article's own last commit**:

```bash
git log -1 --format=%H -- <article>            # the baseline, derived
git diff --name-only <baseline>..HEAD -- <each code_ref>
```

Any output → `status: stale`. This check is mechanical on purpose — no LLM judgment, so no blind spots. A deleted file is a diff hit like any other change, so deletions auto-flag dependents.

**Why derived and not stamped (2026-08-12).** The baseline used to be a stored `verified_sha`. Bumping it creates a new commit, which leaves the stamp pointing one commit too early — a repair commit whose whole content is fixing the field, eight of them in one repo, and unsatisfiable under per-step TDD where a wiki correction may cite code that does not exist yet. Deriving the baseline makes that impossible by construction: **a commit that touches the article and its `code_ref` together is trivially not stale.** It also retires the old `c3` "same commit" check, whose satisfiable half this is.

**The cost, accepted deliberately:** an edit resets the baseline whether or not the Facts were re-read. So **editing a swept article IS re-verifying it** — if you are not re-verifying, do not touch it. Re-verifying without a content change is an appended `## History` line, which at least records what was checked.

**The check is a script** — `python .claude/skills/yourteam/scripts/yt_wiki.py` runs the sweep over all map articles plus its lints: Facts-coverage (every file a Fact cites is inside the article's `code_refs`, else that Fact can rot invisibly), unresolvable citations, amplifier `code_refs`, internal links, and integrity. `sweep --update` rewrites flagged articles to `status: stale`. Exit 0 is the compile-pass precondition.

Run the check:
- At every standup (over all `verified` articles — it's cheap)
- Before building any subagent brief that would consume an article
- **After a story's last commit** — never before. A sweep measured before the final edit is not evidence about the story; it is evidence about a tree that no longer exists.

## Quarantine Rule

`stale` articles are readable but demoted: **their claims never enter a subagent brief.** Briefs include `verified` content only. If everything relevant is stale, the subagent gets no wiki content and explores the code manually — the worst case degrades to "no wiki," never to confidently wrong.

## Forward Blast Radius (code → knowledge), at the DoD Gate

When a story completes:
1. `git diff --name-only <story-start>..<story-end>` → changed paths
2. Match against every **map** article's `code_refs`
3. Every hit is in the blast radius. For each: **update** the article or explicitly **re-verify** it ("read the code, Facts still accurate") — either way the article is touched in the story, which is what moves its baseline.
4. Unresolved blast radius = story does not pass the DoD gate. Staleness cannot accumulate silently; it is mechanically blocked, same as a failing test.

The rule is **same STORY, no false intermediate**: the correction lands within the story, and no intervening commit may leave the repo asserting something false. It is not "same commit" — under strict TDD a correction citing not-yet-written code cannot share a commit with it.

## Reverse Blast Radius (knowledge → code), at Dispatch

Before dispatching an implementer: collect `verified` map articles whose `code_refs` overlap the story's expected files. Their Facts sections go into the brief. This is also the momentum signal at planning ("story touches files we just documented") and the risk signal at refinement (many articles referencing a path = load-bearing code = bump the estimate).

## Sprint-End Compile Pass (blocks review)

Before the review may be called:
1. **Route** the sprint's raw material — story outcomes, review-worthy discoveries, gotchas hit, decisions made — through the four-row table above. Most of it is not a new article: it is a test, a CLAUDE.md line, or a reason. Fold what remains into map articles: update existing, create new ones for concepts that earned them.
2. Rehabilitate or archive remaining `stale` articles touched this sprint.
3. **Link lint** (mechanical): grep internal wiki links, verify each target exists. Broken → repoint to the archive tombstone or prune.
4. Report drift in the retro: articles stale ≥3 sprints get a decision — recompile or archive. An honest gap beats a decaying claim. Report the **map-tier count** too: if it is growing every sprint, row 1 of the routing table is not being used.

Per-story stale-flagging already happened in real time, so batching the *writing* to sprint-end delays nothing safety-critical.

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
- A tombstone is the archetypal `tier: reference` content: it explains a past decision and cites no live line. When a map article is emptied by deletion, what survives is usually one reference article carrying the reason.
- `docs/scrum/sprints/` and `stories/` history is exempt from all of this: append-only records of the past are allowed to reference dead code, like old meeting notes. Only `wiki/` must stay current.
