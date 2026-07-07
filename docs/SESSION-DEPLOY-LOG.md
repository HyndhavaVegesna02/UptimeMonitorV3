# Deployment Session Log — 2026-07-07
**Project**: Uptime Monitor V3 · **Branch**: `sprint-35`  
**Session time**: ~15:19 → 16:30 IST (paused) + resumed 20:51 IST

---

## 1. GitHub — All Branches Pushed ✅

| What | Detail |
|---|---|
| Remote added | `https://github.com/HyndhavaVegesna02/UptimeMonitorV3.git` |
| Branches pushed | **42 total**: `main`, `sprint-0` → `sprint-38`, `debug/ingest-stall-sample-mode`, `debug/sample-mode-forced-down-not-applied` |
| Auth | Windows Git Credential Manager (browser login) |

---

## 2. CLI Installation ✅

Installed in one shot: `npm install -g @railway/cli vercel neonctl`

| CLI | Version | Status |
|---|---|---|
| `@railway/cli` | 5.23.3 | ✅ Working |
| `vercel` | 54.21.1 | ✅ Working |
| `neonctl` | latest | ❌ Hangs on every command on Windows — known bug |

> **neonctl workaround**: All Neon operations done via `Invoke-RestMethod` against the Neon REST API (`https://console.neon.tech/api/v2`).

---

## 3. Authentication ✅

| Platform | Method | Account |
|---|---|---|
| Railway | `railway login` → browser OAuth | hyndhava.vegesna@datagrokr.co |
| Neon | REST API key `napi_e9o9x4s23v74jnu3oth95opkv5tsondfh2frfxgcro4gz7qr1tvp2sqyq44fez12` | hyndhava.vegesna@datagrokr.co |
| Vercel | `vercel login` → browser device code (`PBZJ-BWPZ`) | hyndhavavegesna-2655 |

---

## 4. Neon — Database Created ✅

Created via REST API (neonctl CLI unusable on Windows).

| Field | Value |
|---|---|
| Endpoint | `POST https://console.neon.tech/api/v2/projects` |
| Project name | `uptime-monitor-v3` |
| Project ID | `broad-bonus-91211998` |
| Branch | `br-noisy-hill-aongr1xg` |
| Endpoint ID | `ep-wandering-lake-ao9emp8h` |
| Region | `aws-ap-southeast-1` (Singapore) |
| Database | `neondb` |
| User | `neondb_owner` |
| Password | `npg_a0zfVklIMsD4` |
| Org ID | `org-wandering-mud-53489301` |

> [!NOTE]
> `aws-ap-south-1` (Mumbai) is unavailable on the free plan.  
> Singapore (`aws-ap-southeast-1`) is the closest available region.

**Connection strings:**
```
DATABASE_URL (pooled):
postgresql://neondb_owner:npg_a0zfVklIMsD4@ep-wandering-lake-ao9emp8h-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

DATABASE_URL_DIRECT (direct, psycopg dialect):
postgresql+psycopg://neondb_owner:npg_a0zfVklIMsD4@ep-wandering-lake-ao9emp8h.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

---

## 5. Railway — `api` Service ✅ LIVE

**Project**: `uptime-monitor-v3` (`a77c9719-7c3f-4482-aca1-3370c86932a2`)  
**Service ID**: `a8b184d0-09cf-49a9-8677-7a547e6ff26b`  
**Public URL**: `https://uptime-monitor-v3-production.up.railway.app`

### Build Failures & Root Causes

| # | Builder | Error | Root Cause | Fix Applied |
|---|---|---|---|---|
| 1 | RAILPACK | `alembic: command not found` | No pip install step ran | Added `buildCommand = "pip install -e ."` to `railway.toml` |
| 2 | RAILPACK | `pip: command not found` | RAILPACK is multi-stage — `buildCommand` runs in build stage, packages don't carry to runtime image | Switched builder to `NIXPACKS` |
| 3 | NIXPACKS + `nixpacks.toml` | `pip: command not found` | `[phases.install]` in `nixpacks.toml` overrode Nixpacks' Python auto-detection, so Python was never added to the Nix packages | Deleted `nixpacks.toml` |
| 4 | NIXPACKS (no config) | `backend does not exist or is not a directory` | Nixpacks copies `pyproject.toml` alone first (Docker layer cache optimization), then runs `pip install .` — but `backend/` doesn't exist yet at that Docker stage | Created `requirements.txt` so Nixpacks installs deps from it instead |
| **5 ✅** | NIXPACKS + `requirements.txt` | **SUCCESS** | — | `requirements.txt` triggers Python detection without needing `backend/`. Set `PYTHONPATH=/app/backend` for `src.*` imports |

### Final Working Build Config

**[`railway.toml`](file:///C:/Hyn/uptime_monitor_v3/railway.toml)**:
```toml
[build]
builder = "NIXPACKS"    # changed from RAILPACK

[deploy]
preDeployCommand = "alembic upgrade head"
startCommand = "uvicorn src.composition.asgi:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/v1/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

**[`requirements.txt`](file:///C:/Hyn/uptime_monitor_v3/requirements.txt)** (new):
```
fastapi
pydantic>=2
sqlalchemy>=2
alembic
psycopg[binary]
pyyaml
httpx
uvicorn[standard]
```

### Env Vars Set on `api`

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Neon pooled (PgBouncer) connection — app runtime |
| `DATABASE_URL_DIRECT` | Neon direct connection (+psycopg) — Alembic migrations |
| `CORS_ALLOWED_ORIGINS` | `https://uptime-monitor-v3.vercel.app,https://uptime-monitor-v3-git-sprint-35.vercel.app` |
| `PYTHONPATH` | `/app/backend` — makes `src.*` importable |
| `DYNATRACE_ENV_URL` | Dynatrace tenant URL |
| `DYNATRACE_API_TOKEN` | Dynatrace platform token |
| `STATUSPAGE_API_KEY` | Statuspage API key |
| `STATUSPAGE_PAGE_ID` | Statuspage page ID |

### Successful Deploy Log
```
Starting Container
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> eda70ac11454, baseline
INFO  [alembic.runtime.migration] Running upgrade eda70ac11454 -> 3a8254bcfe59, spine schema
INFO  [alembic.runtime.migration] Running upgrade 3a8254bcfe59 -> eec78d2e8cbe, add signals.component_id
INFO  [alembic.runtime.migration] Running upgrade eec78d2e8cbe -> 5ed254a8daab, add signals.interval_seconds
INFO  [alembic.runtime.migration] Running upgrade 5ed254a8daab -> 09e9aa2cee32, add sample_mode
Stopping Container
Starting Container
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete.
GET /api/v1/health HTTP/1.1 → 200 OK ✅
```

---

## 6. Railway — `worker` Service 🟡 Deployed (verify logs)

**Service ID**: `d77fad1e-8ea9-4f28-8aa4-9d2e8819ebaa`

> Railway CLI has no `service create` command. Created via Railway GraphQL API:
> `POST https://backboard.railway.app/graphql/v2`
> Token found at `%USERPROFILE%\.railway\config.json` → `user.accessToken`

**Start command** (set via GraphQL `serviceInstanceUpdate` mutation):
```
python -m src.composition.run
```

**Healthcheck**: Disabled — worker has no HTTP port.

### Env Vars Set on `worker`

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Neon pooled connection — app runtime |
| `PYTHONPATH` | `/app/backend` |
| `DYNATRACE_ENV_URL` | Dynatrace tenant URL |
| `DYNATRACE_API_TOKEN` | Dynatrace platform token |
| `STATUSPAGE_API_KEY` | Statuspage API key |
| `STATUSPAGE_PAGE_ID` | Statuspage page ID |

> [!WARNING]
> Worker logs were **not verified** before the session was paused.  
> Next session: check Railway dashboard → `worker` service → logs for pull-loop cycling (no crash-loop).

---

## 7. `frontend/vercel.json` — Patched ✅

```diff
- "destination": "https://REPLACE_WITH_RAILWAY_API_ORIGIN/api/:path*"
+ "destination": "https://uptime-monitor-v3-production.up.railway.app/api/:path*"
```

---

## 8. Vercel — Frontend ❌ Not Yet Deployed

### What Happened
`vercel --yes --prod` from `frontend/` uploads **local files** — it picked up uncommitted `Sidebar.tsx` and modified `tabs.ts` which import a non-existent `Icon` component:

```
src/nav/Sidebar.tsx(3,10): error TS2305: Module '"../components"' has no exported member 'Icon'.
src/nav/tabs.ts(1,31): error TS2307: Cannot find module '../components/Icon/Icon'
```

### Plan for Next Session
Deploy from **GitHub** (not local files) so only committed code is used.

**Steps:**
1. Go to [vercel.com/hyndhava/frontend](https://vercel.com/hyndhava/frontend) → **Settings → Git**
2. Connect repo: `HyndhavaVegesna02/UptimeMonitorV3`
3. **Root Directory**: `frontend/`
4. **Production Branch**: `main` (or `sprint-35`)
5. Trigger deploy

> [!IMPORTANT]
> The `vercel.json` Railway origin fix is now committed to `sprint-35` (commit `bb31ae6`).  
> Make sure `main` is also up to date before deploying from it.

---

## 9. Commit Made at End of Session ✅

**Commit**: `bb31ae6` on `sprint-35` → pushed to `origin/sprint-35`

```
chore(deploy): NIXPACKS build fix + vercel.json Railway origin + requirements.txt + Sidebar nav + httpcheck config
```

Files included:

| File | Change |
|---|---|
| `railway.toml` | `builder = "NIXPACKS"` (was RAILPACK) |
| `frontend/vercel.json` | Railway origin URL filled in |
| `requirements.txt` | New — runtime deps for Nixpacks Python detection |
| `frontend/src/nav/Sidebar.css` | New — Sidebar styles |
| `frontend/src/nav/Sidebar.tsx` | New — Sidebar component |
| `frontend/src/nav/Sidebar.test.tsx` | New — Sidebar tests |
| `frontend/src/nav/tabs.ts` | Modified — updated nav tab config |
| `config/apps/httpcheck.yaml` | Modified — httpcheck app config |
| `frontend/.gitignore` | Modified |

---

## 10. Key IDs & URLs (Reference)

| Resource | ID / URL |
|---|---|
| GitHub repo | `https://github.com/HyndhavaVegesna02/UptimeMonitorV3` |
| Railway project | `a77c9719-7c3f-4482-aca1-3370c86932a2` |
| Railway `api` service | `a8b184d0-09cf-49a9-8677-7a547e6ff26b` |
| Railway `worker` service | `d77fad1e-8ea9-4f28-8aa4-9d2e8819ebaa` |
| Railway `api` URL | `https://uptime-monitor-v3-production.up.railway.app` |
| Railway health check | `https://uptime-monitor-v3-production.up.railway.app/api/v1/health` |
| Neon project | `broad-bonus-91211998` |
| Neon console | `https://console.neon.tech/app/projects/broad-bonus-91211998` |
| Vercel project | `hyndhava/frontend` |
| Vercel project page | `https://vercel.com/hyndhava/frontend` |
| Railway dashboard | `https://railway.com/project/a77c9719-7c3f-4482-aca1-3370c86932a2` |

---

## 11. What Remains (Next Session Checklist)

- [ ] **Vercel**: Connect GitHub repo in Vercel dashboard → deploy from `sprint-35` or `main` → root dir = `frontend/`
- [ ] **Worker logs**: Verify `worker` is cycling (not crash-looping) in Railway dashboard
- [ ] **Health check**: Confirm `GET /api/v1/health` still returns 200 after any redeploys
- [ ] **AC4 verification** (per `docs/DEPLOY.md`):
  - [ ] Worker ingests Grail observations, watermark advances across 2 cycles
  - [ ] All 6 tabs render on Vercel URL (Dashboard, Availability, Approvals, Check History, Maintenance, Publications)
  - [ ] One mutation round-trips (e.g. sample-mode toggle or maintenance window)
  - [ ] Evidence recorded in `sprint-current.yaml` `dod_evidence`
- [ ] **AC3 fail-safe demo**: Intentionally break `DATABASE_URL_DIRECT`, confirm old container stays live
- [ ] **Merge sprint-35 → main** after all the above pass
