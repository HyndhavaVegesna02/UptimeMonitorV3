"""Syntactic validation for the sample-mode feature (dossier §13, STORY-048 D3).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md. This module is
present per the five-file convention, but has no active validation rules:
the PUT body's only field (`enabled: bool`) is validated by Pydantic/FastAPI
itself (a missing field or a non-boolean value already 422s at the body-parse
step, before this feature's service ever runs) — mirrors
`api/v1/topology/validation.py`'s no-op-for-the-GET-endpoint pattern.
"""
