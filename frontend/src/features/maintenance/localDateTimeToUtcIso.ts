/**
 * Converts a `<input type="datetime-local">` value (LOCAL wall-clock, no
 * offset — e.g. `"2026-07-22T10:30"`) to a tz-aware UTC ISO string with a
 * trailing `Z` (STORY-132 AC2 — the backend 422s a naive/non-UTC datetime,
 * global API contract fact). `new Date(value)` parses a datetime-local
 * string in the BROWSER's local timezone, and `.toISOString()` always
 * renders UTC with a trailing `Z` — the conversion the API requires.
 */
export function localDateTimeToUtcIso(localValue: string): string {
  return new Date(localValue).toISOString()
}
