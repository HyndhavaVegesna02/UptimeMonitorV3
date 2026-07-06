import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ApiError } from '../api/client'
import type { CreateMaintenanceRequest } from '../api/types'
import { Button, EmptyState, ErrorState, LoadingState, Panel } from '../components'
import { useComponents } from '../features/dashboard/useComponents'
import { fieldErrorFromDetail } from '../features/maintenance/fieldError'
import { useMaintenance } from '../features/maintenance/useMaintenance'
import { deriveWindowState } from '../features/maintenance/windowState'
import type { WindowState } from '../features/maintenance/windowState'
import './MaintenancePage.css'

const WINDOW_STATE_LABEL: Record<WindowState, string> = {
  upcoming: 'Upcoming',
  active: 'Active',
  past: 'Past',
}

/**
 * Tokens-only dot+label state badge (STORY-015f AC1) — deliberately kept
 * SEPARATE from the shell `StatusBadge`/`HealthStatus` vocabulary (which
 * models COMPONENT health: up/down/degraded/maintenance/unknown) rather than
 * a WINDOW's own scheduling state; conflating the two would let an
 * unrelated component-health contract change ripple into this badge's
 * meaning (the same reasoning `observationHealth.ts` documents for keeping
 * ITS vocabulary separate from `toHealthStatus`). The dot is `aria-hidden`
 * — the text label is the sole accessible name, never color alone.
 */
function WindowStateBadge({ state }: { state: WindowState }) {
  return (
    <span className={`maintenance-state-badge maintenance-state-badge--${state}`}>
      <span className="maintenance-state-badge__dot" aria-hidden="true" />
      <span className="maintenance-state-badge__label">{WINDOW_STATE_LABEL[state]}</span>
    </span>
  )
}

/** `reason` is nullable on the wire — render an explicit em-dash rather than
 * a blank cell or the literal string "null" (STORY-015f conventions
 * checklist (h)). */
function formatReason(reason: string | null): string {
  return reason ?? '—'
}

interface ScheduleFormProps {
  onSubmit: (request: CreateMaintenanceRequest) => Promise<boolean>
  scheduling: boolean
  mutationError: ApiError | null
}

/**
 * The schedule-maintenance form (STORY-015f AC2, AC3, AC4). Component
 * options come from the EXISTING `GET /api/v1/components` (`useComponents`,
 * the same source the Dashboard tab uses) — no new fetch shape, per the
 * sprint-34 plan. `starts_at`/`ends_at` are entered as local time
 * (`<input type="datetime-local">`); on submit each is converted to a
 * tz-aware ISO string via `new Date(value).toISOString()` before POSTing —
 * the tz-discipline the backend requires (AC2). A 422's `ApiError.detail` is
 * mapped via `fieldErrorFromDetail` onto the specific field it concerns and
 * rendered INLINE next to that field (AC3, not toast/console-only); a
 * detail naming none of the three fields falls back to a general
 * form-level error banner instead of being silently dropped. On a
 * successful submit the form resets (STORY-015f AC2 — a fresh empty form
 * ready for the next window).
 */
function ScheduleForm({ onSubmit, scheduling, mutationError }: ScheduleFormProps) {
  const { state: componentsState, retry: retryComponents } = useComponents()
  const [componentId, setComponentId] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [reason, setReason] = useState('')

  const erroredField = fieldErrorFromDetail(mutationError?.detail)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const ok = await onSubmit({
      component_id: componentId,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
      reason: reason.trim() === '' ? null : reason,
    })
    if (ok) {
      setComponentId('')
      setStartsAt('')
      setEndsAt('')
      setReason('')
    }
  }

  return (
    <form className="maintenance-form" onSubmit={(event) => void handleSubmit(event)}>
      <h2 className="maintenance-form__title text-h3">Schedule maintenance</h2>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-component">
          Component
        </label>
        {componentsState.phase === 'loading' && (
          <p className="maintenance-form__hint">Loading components…</p>
        )}
        {componentsState.phase === 'error' && (
          <ErrorState message="Could not load components" onRetry={retryComponents} />
        )}
        {componentsState.phase === 'success' && (
          <select
            id="maintenance-component"
            className="maintenance-form__input"
            value={componentId}
            onChange={(event) => setComponentId(event.target.value)}
            required
          >
            <option value="">Select a component…</option>
            {componentsState.data.map((component) => (
              <option key={component.id} value={component.id}>
                {component.name}
              </option>
            ))}
          </select>
        )}
        {erroredField === 'component_id' && mutationError?.detail ? (
          <p className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {mutationError.detail}
          </p>
        ) : null}
      </div>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-starts-at">
          Starts
        </label>
        <input
          id="maintenance-starts-at"
          className="maintenance-form__input"
          type="datetime-local"
          value={startsAt}
          onChange={(event) => setStartsAt(event.target.value)}
          required
        />
        {erroredField === 'starts_at' && mutationError?.detail ? (
          <p className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {mutationError.detail}
          </p>
        ) : null}
      </div>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-ends-at">
          Ends
        </label>
        <input
          id="maintenance-ends-at"
          className="maintenance-form__input"
          type="datetime-local"
          value={endsAt}
          onChange={(event) => setEndsAt(event.target.value)}
          required
        />
        {erroredField === 'ends_at' && mutationError?.detail ? (
          <p className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {mutationError.detail}
          </p>
        ) : null}
      </div>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-reason">
          Reason
        </label>
        <input
          id="maintenance-reason"
          className="maintenance-form__input"
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </div>

      {mutationError && !erroredField ? (
        <p className="maintenance-form__error" role="alert">
          <span className="maintenance-form__error-icon" aria-hidden="true">
            ⚠
          </span>
          {mutationError.detail ?? 'Could not schedule the maintenance window'}
        </p>
      ) : null}

      <Button type="submit" variant="primary" disabled={scheduling}>
        {scheduling ? 'Scheduling…' : 'Schedule window'}
      </Button>
    </form>
  )
}

/**
 * The Maintenance tab (STORY-015f, dossier §17, split-child of STORY-015):
 * lists scheduled maintenance windows (component, start/end, reason, and a
 * client-derived upcoming/active/past state badge — an active window
 * suppresses degradation proposals, so its state must be unmistakable) and
 * a form to schedule a new one. The second mutating tab (015c Approvals
 * precedent): `useMaintenance` owns both the list `useFetch` and the create
 * mutation, calling the list's `retry()` on a successful create so the view
 * always reconciles with the server (AC2).
 */
export function MaintenancePage() {
  const { state, retry, schedule, scheduling, mutationError } = useMaintenance()

  return (
    <Panel title="Maintenance" headingLevel="h1">
      <ScheduleForm onSubmit={schedule} scheduling={scheduling} mutationError={mutationError} />

      {state.phase === 'loading' && <LoadingState label="Loading maintenance windows…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load maintenance windows" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <EmptyState message="No maintenance scheduled" />
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <table className="maintenance-table">
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Starts</th>
              <th scope="col">Ends</th>
              <th scope="col">Reason</th>
              <th scope="col">State</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((window) => (
              <tr key={window.id}>
                <td>{window.component_id}</td>
                <td>
                  <span className="text-mono">{window.starts_at}</span>
                </td>
                <td>
                  <span className="text-mono">{window.ends_at}</span>
                </td>
                <td>{formatReason(window.reason)}</td>
                <td>
                  <WindowStateBadge
                    state={deriveWindowState(window.starts_at, window.ends_at)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
