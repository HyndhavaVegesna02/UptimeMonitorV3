export type MaintenanceFieldName = 'component_id' | 'starts_at' | 'ends_at'

export interface MappedMaintenanceError {
  /** The field the message should attach to inline, or `null` for a
   * form-level banner (no field matched). */
  field: MaintenanceFieldName | null
  message: string
}

const GENERIC_MESSAGE = 'Something went wrong scheduling this window.'

/**
 * Maps `POST /api/v1/maintenance`'s 422 `{ detail }` string to the offending
 * field (STORY-132 AC3 — the crux of this page). ORDER MATTERS: the
 * end-before-start message ("ends_at must be strictly greater than
 * starts_at.") also names "starts_at", so the "strictly greater than" check
 * MUST run before the plain "starts_at" check, or it would wrongly map to
 * `starts_at` instead of the actual offending field, `ends_at` (real server
 * messages captured verbatim from
 * `backend/src/api/v1/maintenance/validation.py` — plan §Maintenance edge
 * behavior).
 */
export function mapMaintenanceError(detail: string | undefined): MappedMaintenanceError {
  if (!detail) {
    return { field: null, message: GENERIC_MESSAGE }
  }

  if (detail.includes('strictly greater than')) {
    return { field: 'ends_at', message: detail }
  }
  if (detail.includes('component_id')) {
    return { field: 'component_id', message: detail }
  }
  if (detail.includes('starts_at')) {
    return { field: 'starts_at', message: detail }
  }
  if (detail.includes('ends_at')) {
    return { field: 'ends_at', message: detail }
  }

  return { field: null, message: detail }
}
