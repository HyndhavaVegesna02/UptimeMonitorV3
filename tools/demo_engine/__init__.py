"""Grail-shaped demo engine (STORY-148, part 1 of 2 — the wire contract).

A local HTTP server that speaks the Dynatrace Grail `execute query` API
faithfully enough that the REAL, unmodified `make_grail_executor`
(`backend/src/adapters/inbound/dynatrace/grail_executor.py`) can talk to it,
and the real ingest path assembles correct `SignalObservation`s from its
rows — standing in for the expired Dynatrace trial (memory:
`dynatrace-trial-expired`). See `tools/demo_engine/README.md` for what this
part covers and what it deliberately does not (that is STORY-176: the
scenario player, the demo fleet config, and the end-to-end loop run).

Lives outside `backend/src/` on purpose (dossier §4) — it can never enter the
production image, and every module here is free to import `src.*` (the
reverse is never true: nothing under `backend/src/` imports this package).
"""
