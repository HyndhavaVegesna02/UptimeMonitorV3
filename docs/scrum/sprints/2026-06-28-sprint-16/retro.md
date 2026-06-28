# Sprint 16 — Retrospective

**Outcome:** 5/5 points accepted (STORY-040a). The §7 Option-C config layer — `config/apps/*.yaml` +
fail-fast loader/validator + in-memory resolvers (`signal_key→component_id`,
`component→AntiFlapThresholds`) — is live, **unblocking the pipeline orchestration (STORY-016a)**.
Velocity history now `…, 6, 5, 5`; last-3 mean **5.33** (the dip is deliberate: sprints 15/16 were
light by design to de-risk the read-API edge and the brand-new config subsystem).

## What went well
- **First clean sprint in a while:** STORY-040a passed both Opus reviewers on the FIRST pass — no fix
  loop. The gnarliest unbuilt area (a new config subsystem + format design) landed coherently.
- The quality reviewer specifically confirmed `yaml.safe_load` (no unsafe deserialization), that the
  `model_validator`s genuinely fire on each invalid shape, and that the cross-app uniqueness check is
  real — exactly the load-bearing correctness points.
- The Sonnet-implementer path produced clean work; the orchestrator's mechanical re-verification + the
  Opus reviewers remain the safety net.

## What surfaced
1. **Incomplete wiki blast-radius, again.** The implementer seeded `config-layer.md` + re-verified
   `dev-setup-and-dod`, but missed that `api-five-file-convention` + `architecture-boundary` also carry
   `pyproject.toml` in their `code_refs` (stale on the `pyyaml` add; Facts unchanged). The
   orchestrator's compile-pass **staleness sweep** caught it — the SAME class as Sprint 14 (a shared
   `conftest.py` drift was missed). Root cause: when a story touches a SHARED file
   (`pyproject.toml`/`conftest.py`/`CLAUDE.md`), the obvious article gets updated and the others
   sharing that file are missed.
2. The implementer used a YAML block-list `code_refs` style instead of the project's inline `[...]`
   (normalized at the compile pass; it also tripped the sweep's parser).

No blockers, no effort-cap trips, no hotfixes.

## Process change (PO-approved)
1. **New working agreement (2026-06-28):** the wiki blast-radius check is the MECHANICAL staleness
   sweep (run the script over all articles; update/re-verify EVERY stale one) — not eyeballing which
   article to touch. Especially for shared files. Wiki `code_refs` use the inline `[...]` style so the
   sweep parses them. (Generalizes the Sprint 14 + Sprint 16 misses; makes blast-radius a mechanical
   gate.)

## Next
- **STORY-016a — pipeline orchestration** is now unblocked (it consumes the new config resolvers) and
  is the natural Sprint 17 centerpiece: wire observations → collapse → streak → anti-flap → decide per
  cycle → proposals, fake-testable, no live creds. A meatier ~5.
- **STORY-040** (DB topology seed + signal→component migration) — independent; populates the spine for
  the dashboard.
- Then creds/account-gated: STORY-016 (live demo), STORY-017 (deploy). Frontend (STORY-015) still
  deferred until backend is done.
