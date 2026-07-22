import { useCallback, useState } from 'react'
import { ApiError, postMaintenance } from '../../api/client'
import { localDateTimeToUtcIso } from './localDateTimeToUtcIso'
import type { MaintenanceFieldName } from './mapMaintenanceError'
import { mapMaintenanceError } from './mapMaintenanceError'

type Phase = 'idle' | 'submitting'

export interface ScheduleMaintenanceValues {
  componentId: string
  /** Raw `<input type="datetime-local">` values (LOCAL wall-clock). */
  startsAtLocal: string
  endsAtLocal: string
  title: string
  reason: string
}

export interface UseScheduleMaintenanceResult {
  phase: Phase
  fieldErrors: Partial<Record<MaintenanceFieldName, string>>
  /** A detail that named none of the three fields — rendered as a
   * form-level banner instead of an inline field error. */
  formError: string | null
  /** Validates, converts, and POSTs. Returns `true` on a genuine 201
   * success (the caller resets the uncontrolled form and re-fetches the
   * list) and `false` on any rejection (client-side guard OR server 422) —
   * NEVER throws (AC4 applies to every mutating hook on this page, not only
   * the delete path). */
  submit: (values: ScheduleMaintenanceValues) => Promise<boolean>
}

/**
 * The Maintenance schedule-form's submit state machine (STORY-132 AC2/AC3).
 * Client-side guards `component_id` non-blank and `ends_at > starts_at`
 * BEFORE ever calling the API (AC3); a server 422 is mapped through
 * `mapMaintenanceError` (the order-sensitive field mapping is THE crux of
 * this page — see that module). Blank optional `title`/`reason` are sent as
 * `null`, never an empty string (mirrors the DTO's nullable-not-empty
 * convention).
 */
export function useScheduleMaintenance(onScheduled: () => void): UseScheduleMaintenanceResult {
  const [phase, setPhase] = useState<Phase>('idle')
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<MaintenanceFieldName, string>>>({})
  const [formError, setFormError] = useState<string | null>(null)

  const submit = useCallback(
    async (values: ScheduleMaintenanceValues): Promise<boolean> => {
      setFormError(null)
      setFieldErrors({})

      const nextFieldErrors: Partial<Record<MaintenanceFieldName, string>> = {}
      if (!values.componentId.trim()) {
        nextFieldErrors.component_id = 'Choose a component.'
      }
      if (!values.startsAtLocal) {
        nextFieldErrors.starts_at = 'Start is required.'
      }
      if (!values.endsAtLocal) {
        nextFieldErrors.ends_at = 'End is required.'
      }
      if (
        values.startsAtLocal &&
        values.endsAtLocal &&
        new Date(values.endsAtLocal).getTime() <= new Date(values.startsAtLocal).getTime()
      ) {
        nextFieldErrors.ends_at = 'End must be after the start.'
      }

      if (Object.keys(nextFieldErrors).length > 0) {
        setFieldErrors(nextFieldErrors)
        return false
      }

      setPhase('submitting')
      try {
        await postMaintenance({
          component_id: values.componentId,
          starts_at: localDateTimeToUtcIso(values.startsAtLocal),
          ends_at: localDateTimeToUtcIso(values.endsAtLocal),
          title: values.title.trim() ? values.title.trim() : null,
          reason: values.reason.trim() ? values.reason.trim() : null,
        })
        setPhase('idle')
        onScheduled()
        return true
      } catch (err) {
        setPhase('idle')
        const apiErr = err instanceof ApiError ? err : undefined
        const mapped = mapMaintenanceError(apiErr?.detail)
        if (mapped.field) {
          setFieldErrors({ [mapped.field]: mapped.message })
        } else {
          setFormError(mapped.message)
        }
        return false
      }
    },
    [onScheduled],
  )

  return { phase, fieldErrors, formError, submit }
}
