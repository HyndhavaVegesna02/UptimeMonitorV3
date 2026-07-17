/**
 * Location-id display formatting (STORY-098 AC4, dossier §17): raw vendor
 * synthetic-monitor location ids (e.g. `SYNTHETIC_LOCATION-0000000000000047`)
 * dominate two tables. This shortens ANY location id to a generic
 * "Location …tail" display form, derived from the TAIL of the id string —
 * deliberately not a vendor-specific mapping (no lookup table, no
 * `SYNTHETIC_LOCATION`-prefix special-casing) so a future vendor's location
 * id shape shortens the same way. Callers pair the short label with the raw
 * id as a tooltip/`title` so the exact original value is never lost.
 */

/** How many trailing characters of the raw id form the short display tail. */
const TAIL_LENGTH = 4

/**
 * Shortens `locationId` to `"Location …<tail>"`. An id at or under
 * `TAIL_LENGTH` characters is used whole (nothing meaningful left to trim).
 * Empty input renders as the empty string, never a crash or a fabricated
 * label.
 */
export function formatLocationLabel(locationId: string): string {
  if (locationId === '') {
    return ''
  }
  const tail = locationId.length <= TAIL_LENGTH ? locationId : locationId.slice(-TAIL_LENGTH)
  return `Location …${tail}`
}
