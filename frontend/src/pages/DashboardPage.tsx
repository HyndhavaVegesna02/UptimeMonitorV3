import { toHealthStatus } from '../api/statusMapping'
import { EmptyState, ErrorState, LoadingState, Panel, StatusBadge } from '../components'
import { useComponents } from '../features/dashboard/useComponents'
import './DashboardPage.css'

/**
 * The Dashboard tab (STORY-015b): every monitored component with its
 * current health, at a glance. Fetches `GET /api/v1/components` via
 * `useComponents` and renders one row per component — name + status badge
 * (dot/icon + label, never color alone) — in a semantic table so both
 * screen-reader and sighted keyboard users can navigate it (AC1). This is
 * the per-tab pattern 015c–015g copy: page in `pages/`, fetch hook in
 * `features/<tab>/`, shell primitives for loading/empty/error states.
 */
export function DashboardPage() {
  const { state, retry } = useComponents()

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
                  <StatusBadge status={toHealthStatus(component.status)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
