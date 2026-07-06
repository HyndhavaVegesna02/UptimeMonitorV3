export type MaintenanceFormField = 'component_id' | 'starts_at' | 'ends_at'

/**
 * Maps a raw backend validation `ApiError.detail` message (STORY-015f AC3)
 * onto the specific schedule-form field it concerns, so the form can render
 * the error INLINE next to that field rather than as a toast/console-only
 * failure. The two real backend 422 cases both name the offending field in
 * their message text (`api/v1/maintenance/validation.py`:
 * "component_id must be a non-empty string.", "starts_at/ends_at must be
 * timezone-aware."; `core/domain/maintenance.py`'s tz-aware-UTC re-check
 * uses slightly different wording but still names the field) — matched by
 * substring rather than an exact-string allowlist, so a backend wording
 * tweak doesn't silently stop matching. Returns `null` when `detail` is
 * absent (non-422 failure) or names none of the three fields, so the caller
 * can fall back to a general form-level error instead of dropping it.
 */
export function fieldErrorFromDetail(detail: string | undefined): MaintenanceFormField | null {
  if (!detail) {
    return null
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
