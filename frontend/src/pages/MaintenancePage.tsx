import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ApiError } from '../api/client'
import type { CreateMaintenanceRequest, MaintenanceWindowDTO } from '../api/types'
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, Panel } from '../components'
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
  const [reason, setReason] = useState('')
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
      title: title.trim() === '' ? null : title,
      reason: reason.trim() === '' ? null : reason,
    })
    if (ok) {
      setTitle('')
      setReason('')
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
        <label className="maintenance-form__label" htmlFor="maintenance-reason">
          Reason / Notes
        </label>
        <input
          id="maintenance-reason"
          className="maintenance-form__input"
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="e.g. Postgres upgrade reason"
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
            aria-invalid={erroredField === 'component_id'}
            aria-describedby={erroredField === 'component_id' ? 'maintenance-component-error' : undefined}
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
          <p id="maintenance-component-error" className="maintenance-form__error" role="alert">
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
          aria-invalid={erroredField === 'starts_at'}
          aria-describedby={erroredField === 'starts_at' ? 'maintenance-start-error' : undefined}
        />
        {erroredField === 'starts_at' && mutationError?.detail ? (
          <p id="maintenance-start-error" className="maintenance-form__error" role="alert">
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
          aria-invalid={erroredField === 'ends_at'}
          aria-describedby={erroredField === 'ends_at' ? 'maintenance-end-error' : undefined}
        />
        {erroredField === 'ends_at' && mutationError?.detail ? (
          <p id="maintenance-end-error" className="maintenance-form__error" role="alert">
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

function MaintenanceWindowRow({
  window,
  onDelete,
  deleting,
}: {
  window: MaintenanceWindowDTO
  onDelete: (id: number) => Promise<boolean>
  deleting: boolean
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleDeleteClick() {
    if (confirmDelete) {
      await onDelete(window.id)
      setConfirmDelete(false)
    } else {
      setConfirmDelete(true)
    }
  }

  return (
    <li className="maintenance-window">
      <div className="maintenance-window__row-content">
        <div className="maintenance-window__body">
          <div className="maintenance-window__head">
            <span className="maintenance-window__title text-body">
              {window.title ?? '—'}
            </span>
            <WindowStateBadge
              state={deriveWindowState(window.starts_at, window.ends_at)}
            />
          </div>
          {window.reason && (
            <div className="maintenance-window__reason text-caption">
              {window.reason}
            </div>
          )}
          <div className="maintenance-window__meta text-mono text-caption">
            <span>{window.component_id}</span>
            <span aria-hidden="true"> · </span>
            <span>
              {window.starts_at}–{window.ends_at}
            </span>
          </div>
        </div>
        <div className="maintenance-window__actions">
          {confirmDelete ? (
            <div className="maintenance-window__confirm">
              <span className="maintenance-window__confirm-label text-caption">Confirm?</span>
              <Button
                variant="primary"
                disabled={deleting}
                onClick={() => void handleDeleteClick()}
              >
                Yes
              </Button>
              <Button
                variant="secondary"
                disabled={deleting}
                onClick={() => setConfirmDelete(false)}
              >
                No
              </Button>
            </div>
          ) : (
            <Button
              variant="secondary"
              onClick={() => setConfirmDelete(true)}
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </li>
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
  const {
    state,
    retry,
    schedule,
    scheduling,
    mutationError,
    deleteWindow,
    deletingId,
    deleteError,
  } = useMaintenance()

  return (
    <div className="maintenance-page page">
      <PageHeader
        title="Maintenance"
        subtitle="Windows suppress alerting for affected components to prevent false proposals."
      />

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

          {deleteError && (
            <div className="maintenance-window-error text-caption" role="alert">
              <span className="maintenance-window-error__icon">⚠</span>
              {deleteError.detail ?? 'Could not delete the maintenance window'}
            </div>
          )}

          {state.phase === 'loading' && <LoadingState label="Loading maintenance windows…" />}

          {state.phase === 'error' && (
            <ErrorState message="Could not load maintenance windows" onRetry={retry} />
          )}

          {state.phase === 'success' && state.data.length === 0 && (
            <EmptyState
              icon="maintenance"
              message="No maintenance scheduled"
              detail="Schedule a window to suppress alerts during planned work."
            />
          )}

          {state.phase === 'success' && state.data.length > 0 && (
            <ul className="maintenance-window-list">
              {state.data.map((window) => (
                <MaintenanceWindowRow
                  key={window.id}
                  window={window}
                  onDelete={deleteWindow}
                  deleting={deletingId === window.id}
                />
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}
