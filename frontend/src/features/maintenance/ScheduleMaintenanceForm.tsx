import { CalendarBlank } from '@phosphor-icons/react'
import { useId, useRef } from 'react'
import type { FormEvent } from 'react'
import { getComponents } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { useFetch } from '../../lib/useFetch'
import type { ScheduleMaintenanceValues } from './useScheduleMaintenance'
import { useScheduleMaintenance } from './useScheduleMaintenance'
import './ScheduleMaintenanceForm.css'

export interface ScheduleMaintenanceFormProps {
  /** Called after a genuine 201 success — the page re-fetches the windows
   * list from the server (AC2: reconcile, never optimistic-only). */
  onScheduled: () => void
}

function readFormValues(form: HTMLFormElement): ScheduleMaintenanceValues {
  const data = new FormData(form)
  return {
    componentId: String(data.get('component_id') ?? ''),
    startsAtLocal: String(data.get('starts_at') ?? ''),
    endsAtLocal: String(data.get('ends_at') ?? ''),
    title: String(data.get('title') ?? ''),
    reason: String(data.get('reason') ?? ''),
  }
}

/**
 * The schedule-maintenance form (STORY-132 AC2/AC3/AC6) — component select
 * (from its OWN `getComponents` fetch, so this region's loading/error is
 * independent of the windows list's, per AC5), start/end `datetime-local`
 * inputs, optional title/reason. Inputs are UNCONTROLLED (a `ref`-held
 * `<form>` read via `FormData` on submit, vercel-react-best-practices) —
 * only the submit-phase and field-error STATE is tracked in React, never a
 * value-per-keystroke. Field errors carry `aria-invalid` +
 * `aria-describedby` + `role="alert"` (web-design-guidelines); a detail
 * naming no field renders as a form-level banner instead.
 *
 * Start/End (STORY-142 AC1) keep the SAME `<input type="datetime-local">`
 * control — the STORY-132 datetime-local->UTC-Z value contract is
 * byte-identical — wrapped in a styled `.schedule-maintenance-form__datetime`
 * container (leading calendar icon, consistent border/height) so the native
 * OS picker chrome no longer clashes with the rest of the form system.
 */
export function ScheduleMaintenanceForm({ onScheduled }: ScheduleMaintenanceFormProps) {
  const componentsFetch = useFetch(getComponents)
  const schedule = useScheduleMaintenance(onScheduled)
  const formRef = useRef<HTMLFormElement>(null)

  const componentId = useId()
  const startsAtId = useId()
  const endsAtId = useId()
  const titleId = useId()
  const reasonId = useId()
  const componentErrorId = useId()
  const startsAtErrorId = useId()
  const endsAtErrorId = useId()
  const formErrorId = useId()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = readFormValues(event.currentTarget)
    const ok = await schedule.submit(values)
    if (ok) {
      formRef.current?.reset()
    }
  }

  if (componentsFetch.state.phase === 'loading') {
    return <LoadingState label="Loading components…" />
  }
  if (componentsFetch.state.phase === 'error') {
    return <ErrorState message={componentsFetch.state.message} onRetry={componentsFetch.retry} />
  }
  if (componentsFetch.state.data.length === 0) {
    return (
      <EmptyState
        message="No components available"
        detail="A maintenance window needs a monitored component to attach to."
      />
    )
  }

  return (
    <form ref={formRef} className="schedule-maintenance-form" onSubmit={(event) => void handleSubmit(event)}>
      {schedule.formError ? (
        <p id={formErrorId} className="schedule-maintenance-form__banner" role="alert">
          {schedule.formError}
        </p>
      ) : null}

      <div className="schedule-maintenance-form__field">
        <label htmlFor={componentId}>Component</label>
        <select
          id={componentId}
          name="component_id"
          defaultValue=""
          aria-invalid={Boolean(schedule.fieldErrors.component_id)}
          aria-describedby={schedule.fieldErrors.component_id ? componentErrorId : undefined}
        >
          <option value="" disabled>
            Select a component…
          </option>
          {componentsFetch.state.data.map((component) => (
            <option key={component.id} value={component.id}>
              {component.name}
            </option>
          ))}
        </select>
        {schedule.fieldErrors.component_id ? (
          <p id={componentErrorId} className="schedule-maintenance-form__field-error" role="alert">
            {schedule.fieldErrors.component_id}
          </p>
        ) : null}
      </div>

      <div className="schedule-maintenance-form__row">
        <div className="schedule-maintenance-form__field">
          <label htmlFor={startsAtId}>Start</label>
          <div className="schedule-maintenance-form__datetime">
            <Icon icon={CalendarBlank} aria-hidden className="schedule-maintenance-form__datetime-icon" />
            <input
              id={startsAtId}
              name="starts_at"
              type="datetime-local"
              aria-invalid={Boolean(schedule.fieldErrors.starts_at)}
              aria-describedby={schedule.fieldErrors.starts_at ? startsAtErrorId : undefined}
            />
          </div>
          {schedule.fieldErrors.starts_at ? (
            <p id={startsAtErrorId} className="schedule-maintenance-form__field-error" role="alert">
              {schedule.fieldErrors.starts_at}
            </p>
          ) : null}
        </div>

        <div className="schedule-maintenance-form__field">
          <label htmlFor={endsAtId}>End</label>
          <div className="schedule-maintenance-form__datetime">
            <Icon icon={CalendarBlank} aria-hidden className="schedule-maintenance-form__datetime-icon" />
            <input
              id={endsAtId}
              name="ends_at"
              type="datetime-local"
              aria-invalid={Boolean(schedule.fieldErrors.ends_at)}
              aria-describedby={schedule.fieldErrors.ends_at ? endsAtErrorId : undefined}
            />
          </div>
          {schedule.fieldErrors.ends_at ? (
            <p id={endsAtErrorId} className="schedule-maintenance-form__field-error" role="alert">
              {schedule.fieldErrors.ends_at}
            </p>
          ) : null}
        </div>
      </div>

      <div className="schedule-maintenance-form__field">
        <label htmlFor={titleId}>Title (optional)</label>
        <input id={titleId} name="title" type="text" placeholder="e.g. Planned DB maintenance" />
      </div>

      <div className="schedule-maintenance-form__field">
        <label htmlFor={reasonId}>Reason (optional)</label>
        <textarea id={reasonId} name="reason" rows={2} placeholder="e.g. DB upgrade" />
      </div>

      <div className="schedule-maintenance-form__actions">
        {/* A plain native submit button (not the shared `Button` primitive,
           which hardcodes `type="button"` so it never accidentally submits
           a surrounding form elsewhere in the app) — this is the one call
           site that genuinely needs `type="submit"`. Same visual classes
           `Button` itself applies. */}
        <button type="submit" className="button button--primary" disabled={schedule.phase === 'submitting'}>
          {schedule.phase === 'submitting' ? 'Scheduling…' : 'Schedule maintenance'}
        </button>
      </div>
    </form>
  )
}
