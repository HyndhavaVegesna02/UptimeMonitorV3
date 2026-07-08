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
 * Tokens-only dot+label state badge (STORY-015f AC1, carried into the
 * STORY-061 list redesign unchanged) — deliberately kept SEPARATE from the
 * shell `StatusBadge`/`HealthStatus` vocabulary (which models COMPONENT
 * health: up/down/degraded/maintenance/unknown) rather than a WINDOW's own
 * scheduling state; conflating the two would let an unrelated
 * component-health contract change ripple into this badge's meaning. The
 * dot is `aria-hidden` — the text label is the sole accessible name, never
 * color alone.
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
 * checklist (h)). The mock's "Title" field maps directly onto this field
 * (AC1 — the DTO has no separate title). */
function formatReason(reason: string | null): string {
  return reason ?? '—'
}

interface ScheduleFormProps {
  onSubmit: (request: CreateMaintenanceRequest) => Promise<boolean>
  scheduling: boolean
  mutationError: ApiError | null
}

/**
 * The "New window" schedule form (STORY-061 AC1/AC2, rebuilt from STORY-015f/
 * STORY-052's field-mapping logic onto the mock's field order/labels: Title,
 * Component, Start, End). "Title" is a client-only label — there is no
 * separate title field on `CreateMaintenanceRequest`; it is submitted as
 * `reason` (AC1). Component options come from the EXISTING
 * `GET /api/v1/components` (`useComponents`, the same source the Dashboard
 * tab uses) — no new fetch shape. `starts_at`/`ends_at` are entered as local
 * time (`<input type="datetime-local">`); on submit each is converted to a
 * tz-aware ISO string via `new Date(value).toISOString()` before POSTing —
 * the tz-discipline the backend requires (AC2, unchanged from STORY-015f).
 * A 422's `ApiError.detail` is mapped via `fieldErrorFromDetail` onto the
 * specific field it concerns and rendered INLINE next to that field (AC2,
 * not toast/console-only); a detail naming none of the three fields
 * (`component_id`/`starts_at`/`ends_at` — `reason`/Title is never a 422
 * target) falls back to a general form-level error banner instead of being
 * silently dropped. On a successful submit the form resets (AC2 — a fresh
 * empty form ready for the next window).
 */
function ScheduleForm({ onSubmit, scheduling, mutationError }: ScheduleFormProps) {
  const { state: componentsState, retry: retryComponents } = useComponents()
  const [title, setTitle] = useState('')
  const [componentId, setComponentId] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')

  const erroredField = fieldErrorFromDetail(mutationError?.detail)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const ok = await onSubmit({
      component_id: componentId,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
      reason: title.trim() === '' ? null : title,
    })
    if (ok) {
      setTitle('')
      setComponentId('')
      setStartsAt('')
      setEndsAt('')
    }
  }

  return (
    <form className="maintenance-form" onSubmit={(event) => void handleSubmit(event)}>
      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-title">
          Title
        </label>
        <input
          id="maintenance-title"
          className="maintenance-form__input"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. Postgres upgrade"
        />
      </div>

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
            <option value="">Select component…</option>
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
        <label className="maintenance-form__label" htmlFor="maintenance-start">
          Start
        </label>
        <input
          id="maintenance-start"
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
        <label className="maintenance-form__label" htmlFor="maintenance-end">
          End
        </label>
        <input
          id="maintenance-end"
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
 * The Maintenance tab (STORY-061, sprint-38 Operator Dashboard redesign;
 * rebuilds STORY-015f/STORY-052's single-column form+table onto the mock's
 * two-column layout — dossier §17, reference mock's `isMaintenance`
 * section): a "New window" form card on the left, and a windows list on the
 * right — each entry showing its title/reason, a client-derived
 * upcoming/active/past state badge (`deriveWindowState` — an active window
 * suppresses degradation proposals, so its state must be unmistakable), and
 * `component · range`. The per-window delete control is OMITTED (AC3 — no
 * `DELETE /api/v1/maintenance/{id}` on the wire) → deferred to STORY-065.
 * `useMaintenance` owns both the list `useFetch` and the create mutation,
 * calling the list's `retry()` on a successful create so the view always
 * reconciles with the server (AC2, unchanged from STORY-015f/015c).
 */
export function MaintenancePage() {
  const { state, retry, schedule, scheduling, mutationError } = useMaintenance()

  return (
    <div className="maintenance-page">
      <div className="maintenance-page__header">
        <h1 className="text-h1 maintenance-page__title">Maintenance</h1>
        <p className="text-caption maintenance-page__subtitle">
          Windows suppress alerting for affected components to prevent false proposals.
        </p>
      </div>

      <div className="maintenance-page__layout">
        <Panel
          title="New window"
          headingLevel="h2"
          className="maintenance-page__form-panel"
        >
          <ScheduleForm onSubmit={schedule} scheduling={scheduling} mutationError={mutationError} />
        </Panel>

        <Panel className="maintenance-page__list-panel">
          <h2 className="sr-only">Scheduled windows</h2>

          {state.phase === 'loading' && <LoadingState label="Loading maintenance windows…" />}

          {state.phase === 'error' && (
            <ErrorState message="Could not load maintenance windows" onRetry={retry} />
          )}

          {state.phase === 'success' && state.data.length === 0 && (
            <EmptyState message="No maintenance scheduled" />
          )}

          {state.phase === 'success' && state.data.length > 0 && (
            <ul className="maintenance-window-list">
              {state.data.map((window) => (
                <li key={window.id} className="maintenance-window">
                  <div className="maintenance-window__head">
                    <span className="maintenance-window__title text-body">
                      {formatReason(window.reason)}
                    </span>
                    <WindowStateBadge
                      state={deriveWindowState(window.starts_at, window.ends_at)}
                    />
                  </div>
                  <div className="maintenance-window__meta text-mono text-caption">
                    <span>{window.component_id}</span>
                    <span aria-hidden="true"> · </span>
                    <span>
                      {window.starts_at}–{window.ends_at}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}
