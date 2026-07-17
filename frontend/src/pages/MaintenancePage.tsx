import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { ApiError } from '../api/client'
import type { CreateMaintenanceRequest, MaintenanceWindowDTO } from '../api/types'
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Panel,
  Toast,
} from '../components'
import { useComponents } from '../features/dashboard/useComponents'
import type { MaintenanceFormField } from '../features/maintenance/fieldError'
import { fieldErrorFromDetail, validateMaintenanceForm } from '../features/maintenance/fieldError'
import { useMaintenance } from '../features/maintenance/useMaintenance'
import { deriveWindowState } from '../features/maintenance/windowState'
import type { WindowState } from '../features/maintenance/windowState'
import { formatLocalRange } from '../lib/formatTime'
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
 *
 * STORY-102 AC4: the form carries `noValidate` — the browser's own bubble
 * UI never fires — and `validateMaintenanceForm` (required Title + Component
 * + Start + End, plus the end-after-start rule) runs FIRST on submit; any
 * failure renders styled inline text under EVERY invalid field and moves
 * focus to the FIRST one (submit order: Title, Component, Start, End),
 * without ever calling `onSubmit`/hitting the network. Only once the client
 * check passes does the existing server round trip happen: a 422's
 * `ApiError.detail` is still mapped via `fieldErrorFromDetail` onto the
 * specific field it concerns (`clientErrors` and the server's `erroredField`
 * share the SAME per-field rendering slot, merged by `fieldMessage` below —
 * they can never both be non-empty for the same field in practice, since a
 * client failure never reaches the server). A detail naming none of the
 * three server-checked fields falls back to a general form-level error
 * banner instead of being silently dropped. On a successful submit the form
 * resets (AC2 — a fresh empty form ready for the next window).
 */
function ScheduleForm({ onSubmit, scheduling, mutationError }: ScheduleFormProps) {
  const { state: componentsState, retry: retryComponents } = useComponents()
  const [title, setTitle] = useState('')
  const [reason, setReason] = useState('')
  const [componentId, setComponentId] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [clientErrors, setClientErrors] = useState<
    Partial<Record<MaintenanceFormField, string>>
  >({})

  const titleRef = useRef<HTMLInputElement>(null)
  const componentRef = useRef<HTMLSelectElement>(null)
  const startRef = useRef<HTMLInputElement>(null)
  const endRef = useRef<HTMLInputElement>(null)
  const fieldRefs = {
    title: titleRef,
    component_id: componentRef,
    starts_at: startRef,
    ends_at: endRef,
  } as const

  const erroredField = fieldErrorFromDetail(mutationError?.detail)

  function fieldMessage(field: MaintenanceFormField): string | undefined {
    return clientErrors[field] ?? (erroredField === field ? mutationError?.detail : undefined)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const errors = validateMaintenanceForm({ title, componentId, startsAt, endsAt })
    if (errors.length > 0) {
      const errorMap: Partial<Record<MaintenanceFormField, string>> = {}
      for (const { field, message } of errors) {
        errorMap[field] = errorMap[field] ?? message
      }
      setClientErrors(errorMap)
      fieldRefs[errors[0].field].current?.focus()
      return
    }

    setClientErrors({})
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
    <form className="maintenance-form" noValidate onSubmit={(event) => void handleSubmit(event)}>
      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-title">
          Title
        </label>
        <input
          id="maintenance-title"
          ref={titleRef}
          className="maintenance-form__input"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. Postgres upgrade"
          required
          aria-invalid={Boolean(fieldMessage('title'))}
          aria-describedby={fieldMessage('title') ? 'maintenance-title-error' : undefined}
        />
        {fieldMessage('title') ? (
          <p id="maintenance-title-error" className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {fieldMessage('title')}
          </p>
        ) : null}
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
            ref={componentRef}
            className="maintenance-form__input"
            value={componentId}
            onChange={(event) => setComponentId(event.target.value)}
            required
            aria-invalid={Boolean(fieldMessage('component_id'))}
            aria-describedby={
              fieldMessage('component_id') ? 'maintenance-component-error' : undefined
            }
          >
            <option value="">Select component…</option>
            {componentsState.data.map((component) => (
              <option key={component.id} value={component.id}>
                {component.name}
              </option>
            ))}
          </select>
        )}
        {fieldMessage('component_id') ? (
          <p id="maintenance-component-error" className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {fieldMessage('component_id')}
          </p>
        ) : null}
      </div>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-start">
          Start
        </label>
        <input
          id="maintenance-start"
          ref={startRef}
          className="maintenance-form__input"
          type="datetime-local"
          value={startsAt}
          onChange={(event) => setStartsAt(event.target.value)}
          required
          aria-invalid={Boolean(fieldMessage('starts_at'))}
          aria-describedby={fieldMessage('starts_at') ? 'maintenance-start-error' : undefined}
        />
        {fieldMessage('starts_at') ? (
          <p id="maintenance-start-error" className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {fieldMessage('starts_at')}
          </p>
        ) : null}
      </div>

      <div className="maintenance-form__field">
        <label className="maintenance-form__label" htmlFor="maintenance-end">
          End
        </label>
        <input
          id="maintenance-end"
          ref={endRef}
          className="maintenance-form__input"
          type="datetime-local"
          value={endsAt}
          onChange={(event) => setEndsAt(event.target.value)}
          required
          aria-invalid={Boolean(fieldMessage('ends_at'))}
          aria-describedby={fieldMessage('ends_at') ? 'maintenance-end-error' : undefined}
        />
        {fieldMessage('ends_at') ? (
          <p id="maintenance-end-error" className="maintenance-form__error" role="alert">
            <span className="maintenance-form__error-icon" aria-hidden="true">
              ⚠
            </span>
            {fieldMessage('ends_at')}
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
  const range = formatLocalRange(window.starts_at, window.ends_at)

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
            <span title={range.tooltip}>{range.text}</span>
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
 * reconciles with the server (AC2, unchanged from STORY-015f/015c). The
 * `component · range` line's range (STORY-098 AC3) renders via
 * `lib/formatTime.ts::formatLocalRange` — absolute LOCAL start–end with an
 * explicit timezone label as the primary text, the raw UTC range in the
 * `title` tooltip; the schedule FORM's `datetime-local` input is unchanged
 * (it was already local — only this display side changes).
 *
 * STORY-102 AC4: a successful create/delete shows the shared `Toast`
 * ("Window scheduled" / "Window deleted") — `toastMessage` is page-local
 * state set only on the SUCCESS path of each mutation (a failure keeps
 * using the existing `role="alert"` inline/banner error rendering, never
 * this toast).
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
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  async function handleSchedule(request: CreateMaintenanceRequest): Promise<boolean> {
    const ok = await schedule(request)
    if (ok) {
      setToastMessage('Window scheduled')
    }
    return ok
  }

  async function handleDelete(id: number): Promise<boolean> {
    const ok = await deleteWindow(id)
    if (ok) {
      setToastMessage('Window deleted')
    }
    return ok
  }

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
          <ScheduleForm
            onSubmit={handleSchedule}
            scheduling={scheduling}
            mutationError={mutationError}
          />
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
                  onDelete={handleDelete}
                  deleting={deletingId === window.id}
                />
              ))}
            </ul>
          )}
        </Panel>
      </div>

      {toastMessage ? (
        <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
      ) : null}
    </div>
  )
}
