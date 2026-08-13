---
id: STORY-225
title: The deployment/infra files are in no article's code_refs — infra/stack.yaml is gated every run but hooked by no wiki article
type: defect
points: null
status: draft
filed: 2026-08-13
sprint: null
---

## Context

Found 2026-08-13 by the STORY-222 quality reviewer, and **created by STORY-222 itself**. Recorded
here rather than fixed in that story because the right fix is a scoping decision, not a one-line
edit — and because STORY-222 was already in a fix round for three other MAJORs.

## The finding

Converting `deployment-and-infra.md` to a `tier: reference` tombstone stripped its `code_refs`.
Those `code_refs` were the **only** wiki hooks these files had. Verified at HEAD:

| Path | In any article's `code_refs`? |
| --- | --- |
| `infra/stack.yaml` | **none** |
| `Dockerfile` | **none** |
| `.dockerignore` | **none** |
| `scripts/create_tables.py` | **none** |
| `scripts/seed_topology.py` | `zone-rules.md` ✔ |

`infra/stack.yaml` is **not dormant**: it is 16 KB, actively maintained, and **cfn-lint runs it as
one of the eight DoD gate commands on every single run**.

## Why it matters

The wiki protocol's forward blast radius works by matching a story's changed paths against every
map article's `code_refs`. A file in no `code_refs` has **zero forward blast radius** — change it
however you like and no article is ever flagged stale, because no article claims to describe it.

So the repo is now in the state the protocol exists to prevent, in a specific way: not
*trusted-and-wrong*, but **unhooked**. Nothing asserts anything about these files, so nothing can
rot — which is technically safe and practically means the deployment surface has no documentation
under maintenance at all.

**This was a real loss, not a theoretical one.** Before STORY-222, `deployment-and-infra.md` held
ten enforced citations into these files and carried `baseline: 0` in the citation ratchet — i.e.
they were pinned and clean. That pin is gone.

## The tension to resolve at refinement

The honest difficulty is that `deployment-and-infra.md` was describing **two different things**:

1. **What the template declares** — `infra/stack.yaml`'s resources, policies, wiring. **Still live,
   still gated, still changing.** This is map-tier content by definition.
2. **What was deployed and running** — the URL, the cluster, the observed behaviour. **Dead as of
   2026-08-13.** This is reference-tier tombstone content.

STORY-222 correctly classified the article as a whole by (2) and de-lined the citations to make
that honest. But (1) went with it, and (1) is exactly the content that should still be under
maintenance.

## Fix direction — decide at refinement

**(a) A new `tier: map` article for the CloudFormation template itself** — e.g.
`infra-stack-template.md`, with `code_refs: [infra/stack.yaml, Dockerfile, .dockerignore,
scripts/create_tables.py]`, describing what the template declares in the present tense. The
tombstone keeps the history. This is the split the content always wanted. Cost: a new map article
is recurring sweep cost, and the protocol's routing table says keep the map tier small.

**(b) Attach the files to an existing map article's `code_refs`.** Cheapest, but likely dishonest —
no current article is *about* the CloudFormation template, and `code_refs` are meant to be the
paths an article describes.

**(c) Accept it and record the acceptance.** Defensible *only if* the deployment surface is
genuinely dormant. It is not — cfn-lint gates it every run, and STORY-090 (CI/CD) was archived on
the assumption the stack could come back.

**A refinement bias, not a decision:** (a) is probably right, but check first whether anyone will
maintain it. An unmaintained map article is worse than an honest gap — that is the whole premise
of the three-state invariant.

## Refinement should settle

1. Which shape, and if (a), who/what keeps it current and what its Facts actually assert.
2. **Whether `Dockerfile` and `.dockerignore` belong with the template at all** — they are build
   inputs, not stack resources, and may deserve different placement or none.
3. Whether the citation ratchet should regain a pin on these files, and at what baseline.
4. **Check for other unhooked-but-gated files before choosing** — this story found four by
   accident while reviewing something else. A systematic sweep ("which gated paths are in no
   `code_refs`?") is cheap and would size the real problem. Do that first; the answer may be
   larger than these four and may change the shape.

## Not in scope

Re-litigating STORY-222's tier decision — it was correct for the article as a whole and was
reviewed twice. Rehabilitating the two remaining `status: stale` articles.
