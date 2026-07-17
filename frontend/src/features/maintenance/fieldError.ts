export type MaintenanceFormField = 'title' | 'component_id' | 'starts_at' | 'ends_at'

/**
 * Maps a raw backend validation `ApiError.detail` message (STORY-015f AC3)
 * onto the specific schedule-form field it concerns, so the form can render
 * the error INLINE next to that field rather than as a toast/console-only
 * failure. The three real backend 422 cases from
 * `api/v1/maintenance/validation.py::validate_maintenance_request` all name
 * the offending field in their message text: "component_id must be a
 * non-empty string.", "starts_at/ends_at must be timezone-aware.", and (as
 * of STORY-052) "ends_at must be strictly greater than starts_at." —
 * `core/domain/maintenance.py`'s tz-aware-UTC re-check uses slightly
 * different wording but still names the field. Matched by substring rather
 * than an exact-string allowlist, so a backend wording tweak doesn't
 * silently stop matching.
 *
 * The ordering message is checked FIRST, before the generic substring scan
 * (STORY-052): it mentions `starts_at` too (as the compared-against field),
 * so a naive scan in field-declaration order would mis-map it onto
 * `starts_at` instead of the field actually at fault, `ends_at`. The same
 * ordering also matters for a raw multi-field detail blob (e.g. a Pydantic
 * `ValidationError`'s `str()`, which STORY-052's backend fix avoids
 * producing for this case but which this function still resolves safely):
 * such a blob's `input_value={...}` echo can contain a `component_id`
 * token ahead of the real message, which the naive scan would surface
 * instead — this ordering check, and the substring scan's fixed field
 * order below, keep the result deterministic and never throwing rather
 * than "correct" for every conceivable input.
 *
 * Returns `null` when `detail` is absent (non-422 failure) or names none of
 * the three fields, so the caller can fall back to a general form-level
 * error instead of dropping it.
 */
export function fieldErrorFromDetail(detail: string | undefined): MaintenanceFormField | null {
  if (!detail) {
    return null
  }
  if (detail.includes('strictly greater than')) {
    return 'ends_at'
  }
  if (detail.includes('component_id')) {
    return 'component_id'
  }
  if (detail.includes('starts_at')) {
    return 'starts_at'
  }
  if (detail.includes('ends_at')) {
    return 'ends_at'
  }
  return null
}

export interface MaintenanceFormValues {
  title: string
  componentId: string
  /** `datetime-local` input value (empty string when unfilled). */
  startsAt: string
  /** `datetime-local` input value (empty string when unfilled). */
  endsAt: string
}

export interface MaintenanceFormFieldError {
  field: MaintenanceFormField
  message: string
}

/**
 * Client-side, pre-submit validation for the schedule form (STORY-102 AC4):
 * required Title + Component + Start + End, plus the end-after-start rule
 * the SERVER already enforces (`fieldErrorFromDetail`'s "strictly greater
 * than" 422 case) — checked here too so a violation is caught before a
 * round trip, with matching copy. Extends this file (rather than a second,
 * separate validator module) since both functions map the exact same
 * `MaintenanceFormField` vocabulary onto a message.
 *
 * Returns an ORDERED array — submit order (Title, Component, Start, End) —
 * of `{field, message}` failures, empty when the form is valid. Order
 * matters: the caller focuses the FIRST entry (AC4's "focus moves to the
 * first invalid field"). A missing End never ALSO reports the ordering
 * violation (the required-check and the ordering-check are mutually
 * exclusive per field — only one message per field, ever).
 */
export function validateMaintenanceForm(
  values: MaintenanceFormValues,
): MaintenanceFormFieldError[] {
  const errors: MaintenanceFormFieldError[] = []

  if (values.title.trim() === '') {
    errors.push({ field: 'title', message: 'Title is required.' })
  }
  if (values.componentId.trim() === '') {
    errors.push({ field: 'component_id', message: 'Component is required.' })
  }
  if (values.startsAt.trim() === '') {
    errors.push({ field: 'starts_at', message: 'Start is required.' })
  }
  if (values.endsAt.trim() === '') {
    errors.push({ field: 'ends_at', message: 'End is required.' })
  } else if (
    values.startsAt.trim() !== '' &&
    new Date(values.endsAt) <= new Date(values.startsAt)
  ) {
    errors.push({ field: 'ends_at', message: 'End must be after start.' })
  }

  return errors
}
