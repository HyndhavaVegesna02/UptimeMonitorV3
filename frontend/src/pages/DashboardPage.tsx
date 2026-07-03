import { toHealthStatus } from '../api/statusMapping'
import { EmptyState, ErrorState, LoadingState, Panel, StatusBadge } from '../components'
import { useComponents } from '../features/dashboard/useComponents'
import { useSampleMode } from '../features/dashboard/useSampleMode'
import './DashboardPage.css'

/**
 * The sample-mode toggle (STORY-049 AC1–AC3): a real switch reflecting
 * `GET /api/v1/sample-mode` on load, PUTting on click and reflecting only
 * the PUT RESPONSE's state (no optimistic flip — AC2). While ON, a
 * tokens-styled warning is shown (icon + ink text, never color-alone —
 * AC3). THIS IS A TEMPORARY FEATURE — see
 * `docs/scrum/wiki/sample-mode.md`'s REMOVAL inventory. Nothing is rendered
 * until the initial GET resolves (loading case); a GET failure falls back
 * to the shell `ErrorState` with retry, matching the components table above.
 */
function SampleModeToggle() {
  const { state, retry, enabled, setEnabled, mutating, mutationError } = useSampleMode()

  if (state.phase === 'loading') {
    return null
  }

  if (state.phase === 'error') {
    return <ErrorState message="Could not load sample mode" onRetry={retry} />
  }

  return (
    <div className="dashboard-sample-mode">
      <button
        type="button"
        role="switch"
        aria-checked={enabled ?? false}
        aria-label="Sample mode"
        disabled={mutating}
        className="dashboard-sample-mode__control"
        onClick={() => void setEnabled(!enabled)}
      >
        <span className="dashboard-sample-mode__track" aria-hidden="true">
          <span className="dashboard-sample-mode__thumb" />
        </span>
        <span className="dashboard-sample-mode__text">Sample mode</span>
      </button>

      {enabled ? (
        <p className="dashboard-sample-mode__warning" role="status">
          <span className="dashboard-sample-mode__warning-icon" aria-hidden="true">
            ⚠
          </span>
          sample mode — signals recorded as DOWN
        </p>
      ) : null}

      {mutationError ? (
        <ErrorState message={mutationError} onRetry={() => void setEnabled(!enabled)} />
      ) : null}
    </div>
  )
}

/**
 * The Dashboard tab (STORY-015b): every monitored component with its
 * current health, at a glance. Fetches `GET /api/v1/components` via
 * `useComponents` and renders one row per component — name + status badge
 * (dot/icon + label, never color alone) — in a semantic table so both
 * screen-reader and sighted keyboard users can navigate it (AC1). This is
 * the per-tab pattern 015c–015g copy: page in `pages/`, fetch hook in
 * `features/<tab>/`, shell primitives for loading/empty/error states.
 * Also hosts the STORY-049 sample-mode toggle (a TEMPORARY feature).
 */
export function DashboardPage() {
  const { state, retry } = useComponents()

  return (
    <Panel title="Dashboard" headingLevel="h1">
      <SampleModeToggle />

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
