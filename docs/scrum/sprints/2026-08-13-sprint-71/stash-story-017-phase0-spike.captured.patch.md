# Captured before dropping — `stash@{0}`, STORY-017 Phase-0 spike

**Dropped 2026-08-14 by PO decision at sprint-71 review.** Captured here first so the content
survives in versioned, visible storage rather than a local-only stash.

## Stash metadata

```
stash@{0}: On main: STORY-017 Phase-0 spike (CORS middleware + Dockerfile/.dockerignore + boto3) — author unknown, superseded by AWS epic; PO-directed clean 2026-07-14

based on: 55c00bc0458a3bb869a0d3821f1849d4ab5286e7 (2026-07-14)
parent subject: chore(refinement): AWS migration epic — supersede STORY-017, ready STORY-082..089
```

## Why every hunk was superseded (verified 2026-08-14, not assumed)

| Hunk | Status |
| --- | --- |
| `middleware.py` → `install_cors` | **Actively unwanted.** The file now documents why CORS is not needed: dev goes through the Vite proxy, production is same-origin behind CloudFront (STORY-089). |
| `settings.py` → `cors_allowed_origins` | **Cannot apply.** Patches a `Settings` class carrying `database_url` — the Postgres-era class. Today's is DynamoDB (`aws_region`, `dynamo_observations_table`). |
| `pyproject.toml` → boto3 | Already present at `pyproject.toml:16`. |
| `app.py` → CORS wiring | Depends on all three above. |

It was based on a commit whose PARENT is *"supersede STORY-017, ready STORY-082..089"* — so it
was already obsolete the day it was stashed. STORY-017 is `archived`; the AWS deployment it
targeted was decommissioned 2026-08-13.

## Why it was dropped rather than kept

A stash is **not archival storage**: local-only, never pushed, invisible to `git log` and
`git branch --contains` (verified: reachable from nothing). It can vanish silently on a fresh
clone **and** ambush someone who did not know it was there — which it did on 2026-08-13, when a
reviewer's `git stash pop` landed it as merge conflicts across three `backend/src/` files.

## Full patch

```diff
diff --git a/backend/src/api/v1/_shared/middleware.py b/backend/src/api/v1/_shared/middleware.py
index 6a92805..4c24e38 100644
--- a/backend/src/api/v1/_shared/middleware.py
+++ b/backend/src/api/v1/_shared/middleware.py
@@ -2,5 +2,18 @@
 
 Cites: Proposal (2026-07-10) §6.2.
 Intended occupant: STORY-017 (CORS and authentication middleware).
-Currently contains no active logic.
 """
+
+from fastapi import FastAPI
+from fastapi.middleware.cors import CORSMiddleware
+
+
+def install_cors(app: FastAPI, allowed_origins: list[str]) -> None:
+    """Install CORS middleware onto the application."""
+    app.add_middleware(
+        CORSMiddleware,
+        allow_origins=allowed_origins,
+        allow_credentials=True,
+        allow_methods=["*"],
+        allow_headers=["*"],
+    )
diff --git a/backend/src/composition/app.py b/backend/src/composition/app.py
index f216e54..1fd1cd5 100644
--- a/backend/src/composition/app.py
+++ b/backend/src/composition/app.py
@@ -120,6 +120,7 @@ def create_app(
         # Load and validate config (fail-fast: raises if invalid)
         cfg_dir = config_dir or settings.config_dir
         app.state.seed_config = load_config(cfg_dir)
+        app.state.cors_allowed_origins = settings.cors_allowed_origins
     else:
         # Repos were injected (e.g. fakes in tests). Leave component_repo,
         # maintenance_repo, and observation_repo as-passed — possibly None —
@@ -208,4 +209,11 @@ def create_app(
 
     install_error_handlers(app)
 
+    # Install CORS middleware (STORY-017 / Phase 0)
+    from src.api.v1._shared.middleware import install_cors
+    
+    cors_origins = getattr(app.state, "cors_allowed_origins", [])
+    if cors_origins:
+        install_cors(app, cors_origins)
+
     return app
diff --git a/backend/src/composition/settings.py b/backend/src/composition/settings.py
index 588e2c7..5cf1bf5 100644
--- a/backend/src/composition/settings.py
+++ b/backend/src/composition/settings.py
@@ -41,6 +41,7 @@ class Settings:
 
     database_url: str
     config_dir: str
+    cors_allowed_origins: list[str]
 
 
 def load_settings() -> Settings:
@@ -49,10 +50,14 @@ def load_settings() -> Settings:
     Reads the POOLED connection string from ``DATABASE_URL``. Raises
     ``KeyError`` if it is unset — the app must not start without a database URL.
     Also reads config_dir from ``CONFIG_DIR`` env var, defaulting to ``"config/apps"``.
+    Also reads cors_allowed_origins from ``CORS_ALLOWED_ORIGINS`` env var (comma-separated).
     """
+    origins_str = os.environ.get("CORS_ALLOWED_ORIGINS", "")
+    allowed_origins = [o.strip() for o in origins_str.split(",")] if origins_str else []
     return Settings(
         database_url=os.environ[APP_DATABASE_URL_VAR],
         config_dir=os.environ.get("CONFIG_DIR", "config/apps"),
+        cors_allowed_origins=allowed_origins,
     )
 
 
diff --git a/pyproject.toml b/pyproject.toml
index 7c4e3e5..bee3aa9 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -16,6 +16,7 @@ dependencies = [
     "pyyaml",
     "httpx",
     "python-dotenv",
+    "boto3",
 ]
 
 [project.optional-dependencies]
```
