import { toHealthStatus } from '../api/statusMapping'
import type { MaintenanceWindowDTO } from '../api/types'
import { EmptyState, ErrorState, LoadingState, Panel, StatusBadge } from '../components'
import { useComponents } from '../features/dashboard/useComponents'
import { useMaintenanceWindows } from '../features/dashboard/useMaintenanceWindows'
import { deriveWindowState } from '../features/maintenance/windowState'
import './DashboardPage.css'

/**
 * True iff ANY of `windows` belonging to `componentId` is currently ACTIVE
 * per the half-open `deriveWindowState` rule (STORY-046, dossier §6/§11 —
 * health and maintenance are separate concepts, so this never touches
 * `toHealthStatus`/`ComponentStatus`). Multiple windows on one component are
 * OR'd together: any single active window is enough to mark it.
 */
function isUnderActiveMaintenance(
  componentId: string,
  windows: MaintenanceWindowDTO[],
): boolean {
  return windows
    .filter((window) => window.component_id === componentId)
    .some((window) => deriveWindowState(window.starts_at, window.ends_at) === 'active')
}

/**
 * The Dashboard tab (STORY-015b): every monitored component with its
 * current health, at a glance. Fetches `GET /api/v1/components` via
 * `useComponents` and renders one row per component — name + status badge
 * (dot/icon + label, never color alone) — in a semantic table so both
 * screen-reader and sighted keyboard users can navigate it (AC1). This is
 * the per-tab pattern 015c–015g copy: page in `pages/`, fetch hook in
 * `features/<tab>/`, shell primitives for loading/empty/error states.
 * The STORY-049 sample-mode toggle used to live here — STORY-056 relocated
 * it to the shell's `TopBar`/`SampleModeBanner` (still the same
 * `useSampleMode` feature hook, just no longer rendered by this page).
 *
 * STORY-046: ALSO fetches `GET /api/v1/maintenance` via
 * `useMaintenanceWindows` and overlays a maintenance indicator next to a
 * component's health badge when it has an ACTIVE window (never replacing
 * the health badge — dossier §6/§11, health and maintenance are separate
 * concepts). Graceful degradation: a maintenance-fetch failure (or its
 * loading state) must never block the primary components table, so any
 * non-`'success'` maintenance state is treated as "no active windows" —
 * the overlay silently disappears instead of erroring the whole page.
 */
export function DashboardPage() {
  const { state, retry } = useComponents()
  const { state: maintenanceState } = useMaintenanceWindows()
  const maintenanceWindows =
    maintenanceState.phase === 'success' ? maintenanceState.data : []

  return (
    <Panel title="Dashboard" headingLevel="h1">
      {state.phase === 'loading' && <LoadingState label="Loading components…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load components" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <EmptyState message="No components configured" />
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <table className="dashboard-table">
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((component) => (
              <tr key={component.id}>
                <td>{component.name}</td>
                <td>
                  <div className="dashboard-status-cell">
                    <StatusBadge status={toHealthStatus(component.status)} />
                    {isUnderActiveMaintenance(component.id, maintenanceWindows) && (
                      <StatusBadge status="maintenance" label="Under maintenance" />
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
