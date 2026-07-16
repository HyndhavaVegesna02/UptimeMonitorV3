# STORY-095 -- Playwright UI sweep findings

Target: `https://d3ukiib1iqmbxb.cloudfront.net` (LIVE, real AWS us-east-1).
Driven by `tools/ui-sweep/sweep.mjs` (headless Chromium via Playwright,
phase-based: `tabs`, `theme`, `sample-on`, `sample-off`, `maint-create`,
`maint-delete`). All screenshots and `*.evidence.json` (console errors +
failed `/api/*` responses per phase) live alongside this file.

## Per-AC verdict

### AC1 -- six tabs render (deep load + SPA nav) -- PASS

All six tabs render real content or a legitimate empty state, via both a
direct-URL deep load (fresh `page.goto`, exercising the CloudFront rewrite
function) and SPA client-side navigation (clicking the sidebar from an
already-loaded Dashboard). No error boundary, no blank shell, in either
mode.

| Tab | Deep-load evidence | SPA-nav evidence | Rendered state |
| --- | --- | --- | --- |
| Dashboard | `dashboard-deep.png` | `dashboard-spa.png` | Summary cards + component table (1 component, HTTP Check, Up, 98.2x% uptime) |
| Availability | `availability-deep.png` | `availability-spa.png` | Availability vs. data-completeness table with uptime bars |
| Approvals | `approvals-deep.png` | `approvals-spa.png` | "Queue clear -- No proposals awaiting review" (legitimate empty state) |
| Check History | `check-history-deep.png` | `check-history-spa.png` | Filterable observation table, populated rows |
| Maintenance | `maintenance-deep.png` | `maintenance-spa.png` | "New window" form + "No maintenance scheduled" (legitimate empty state, pre-mutation) |
| Publications | `publications-deep.png` | (not separately captured -- identical panel content to the deep load; SPA nav exercised as part of the `spa-session` walk, see `spa-session.evidence.json`) | "Showing the latest 50 publications" list, 1 entry |

Note: the Check History SPA-nav screenshot initially caught a
"Loading observations..." spinner (a real in-flight state, not a bug) because
`networkidle` alone can race a client-side-routed fetch; `sweep.mjs` was
fixed to wait for any "Loading" text to clear before screenshotting SPA
transitions (see the AC1/AC2 commit). Re-run confirms the settled table.

### AC2 -- console + network hygiene -- PASS

Zero console errors and zero failed `/api/*` requests across the entire
sweep -- every phase's `*.evidence.json` has empty `consoleErrors`,
`failedRequests`, and `pageErrors` arrays (verified by scanning all
`*.evidence.json` files for non-empty arrays: none found). No 4xx/5xx was
observed at all, so there is nothing in this sweep needing the
"intentionally-triggered-and-handled" carve-out.

### AC3 -- mutation round-trips via the browser -- PASS

**Sample mode:**
1. Baseline confirmed OFF before any mutation: `aws dynamodb get-item`
   returned `enabled: {"BOOL": false}`.
2. Toggled ON via the top-bar trigger (`sample-mode-before.png` ->
   `sample-mode-on.png`) -- banner "sample mode -- signals recorded as DOWN"
   appears, `aria-checked="true"`. Control table confirmed
   `enabled: {"BOOL": true}`.
3. Toggled OFF (`sample-mode-off.png`) -- banner clears, `aria-checked="false"`.
   Control table confirmed `enabled: {"BOOL": false}` again.
4. A close look at `sample-mode-off.png` at full-page thumbnail scale made
   the trigger button look similarly "filled" to the ON state -- investigated
   with an isolated element screenshot on an independent fresh reload
   (`sample-mode-button-verify.png`) plus `element.className` /
   `aria-checked` inspection: className is `top-bar__button top-bar__trigger`
   (no `--active` modifier), `aria-checked="false"`. **EXPLAINED**: a
   full-page-screenshot-scale visual artifact, not a real state bug -- the
   steady-state style (red outline, light fill) is correct.

**Maintenance window:**
1. Baseline: "No maintenance scheduled" (`maintenance-before.png`).
2. Form filled (Title `ui-sweep-probe`, Reason "STORY-095 automated sweep
   probe -- safe to delete", Component = first available, Start = now+1h,
   End = now+2h) -- `maintenance-form-filled.png` -- submitted.
3. Window appeared in the list as "Upcoming", `http-check`,
   `2026-07-17T00:12:00Z-2026-07-17T01:12:00Z` (`maintenance-created.png`).
4. Deleted via Delete -> Yes confirm (`maintenance-deleted.png`) -- row
   removed from the list.
5. Page reloaded (full `page.reload`, not just optimistic client removal) --
   0 rows matching `ui-sweep-probe` remained (`maintenance-verified-clean.png`,
   script printed "ui-sweep-probe rows remaining after reload: 0" and would
   have thrown if non-zero).

**Live system left clean**: sample mode `enabled: false` (re-verified after
the mutation phases -- see the final verification below), maintenance probe
window fully deleted server-side.

### AC4 -- theme + viewport spot checks -- PASS

- `theme-light.png` -- fresh context, `colorScheme: 'light'` emulated (no
  localStorage override, exercises the system-preference resolution path in
  `frontend/src/theme/resolveTheme.ts`) -- light theme renders correctly.
- `theme-dark.png` -- same, `colorScheme: 'dark'` -- dark theme renders
  correctly (dark background, light text, health colors preserved).
- `theme-toggle-clicked.png` -- secondary check: fresh light-emulated
  context, clicked the in-app theme toggle button (exercises the
  localStorage-override path) -- correctly flips to dark.
- `viewport-390x844.png` -- 390x844 viewport, Dashboard deep-loaded. Page
  renders, no console error, no blank shell. **Anomaly (CANDIDATE-STORY)**:
  the left sidebar does not collapse or hide at this width -- it keeps its
  full desktop pixel width (~210px of the 390px viewport), squeezing the
  main content into a ~180px column. Summary cards stack vertically and are
  individually readable, but the layout is not a genuine mobile-responsive
  treatment. Filed below as a backlog candidate, not a story defect (AC4
  only requires a render sanity check, which passes).

### AC5 -- evidence -- PASS (this file + the screenshots/evidence.json files under this directory)

## Console/network error table

Empty -- zero console errors, zero failed `/api/*` requests were observed
anywhere in the sweep (six tabs x two load modes, four mutation steps,
four theme/viewport checks = 20+ page loads, all clean). See each
`*.evidence.json` alongside its screenshot for the raw per-load capture.

## Anomalies

| # | Description | Status | Notes |
| - | --- | --- | --- |
| 1 | `sample-mode-off.png` full-page screenshot visually resembles the ON (filled) state at thumbnail scale | EXPLAINED | Isolated element screenshot + `aria-checked`/className inspection on an independent fresh reload confirm the correct OFF steady state (`sample-mode-button-verify.png`). No code defect. |
| 2 | 390x844 viewport: sidebar does not collapse/hide, squeezing content into a narrow column | CANDIDATE-STORY | Dashboard (and by extension the other five tabs, not individually re-checked at this width) is not responsive below ~768px. Suggest a backlog story: collapse the sidebar to an icon rail or a hidden/hamburger drawer below a defined breakpoint. Not a defect against this story's AC4 (render sanity check passes -- no blank shell, no console error). |
| 3 | Check History SPA-nav screenshot initially caught a "Loading observations..." spinner mid-fetch | EXPLAINED (tooling, not app) | `networkidle` alone races a client-routed fetch; `sweep.mjs` was corrected to wait for the loading text to clear before screenshotting SPA transitions. Re-run confirms the settled table renders. Not an app-side finding. |

Known pre-existing behavior (per dispatch brief, not re-filed): the
deployed image predates STORY-094 so `/api/v1/history` ignores a `limit`
query param there (not probed in this sweep, no UI surfaces a limit
control); the sample-mode banner appearing when ON is correct, expected
behavior (verified above, not a defect).

## Live-system cleanliness -- final confirmation

- Control table `uptime-monitor-control` / `CONFIG` / `SAMPLE_MODE`:
  `enabled: {"BOOL": false}` (re-checked after the full sweep -- see the
  final report's `aws dynamodb get-item` output).
- Maintenance windows: 0 rows for `ui-sweep-probe` after a full page reload
  (`maintenance-verified-clean.png`); no other windows were touched.
