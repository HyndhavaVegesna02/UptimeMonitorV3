const LABEL_TAIL_LENGTH = 4

/**
 * Shortens a probe-location id (e.g.
 * `SYNTHETIC_LOCATION-0000000000000060`, the real shape from
 * `ObservationDTO.location`) to a readable short-id presentation
 * (`#0060`) — a `#`-prefixed tail, the same idiom as a ticket/PR number,
 * read as "a deliberate short id" rather than the prior ellipsis-prefixed
 * tail (`…0060`, STORY-122 AC3/AC5), which reads as "truncated, something
 * is hidden" (STORY-140 AC3, 2026-07-22 design-QA review).
 *
 * IMPORTANT — this is still only an id, not a name: a true human-readable
 * location name (e.g. "Frankfurt, DE") requires a `location_name` field the
 * `/api/v1` wire contract does not carry today (`ObservationDTO.location`
 * is the raw synthetic-location id, nothing else). Inventing a name
 * client-side would misrepresent data the API never sent, so this
 * function stays an id-presentation improvement only. The true fix is
 * filed as STORY-144 (backend: add `location_name` to the observation/
 * availability API) — see STORY-140's story-file History for the record.
 */
export function locationLabel(location: string): string {
  if (location.length <= LABEL_TAIL_LENGTH) {
    return location
  }
  return `#${location.slice(-LABEL_TAIL_LENGTH)}`
}
