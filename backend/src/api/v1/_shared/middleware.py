"""Seam for shared API middleware (e.g. authentication).

Cites: Proposal (2026-07-10) §6.2.
No CORS middleware is required: dev traffic goes through the Vite dev-server
proxy (vite.config.ts), and production is same-origin behind CloudFront
(STORY-089). This file remains a documented seam for future middleware —
e.g. authentication, which has no story assigned yet (see
`frontend/src/api/actor.ts`). Currently contains no active logic.
"""
