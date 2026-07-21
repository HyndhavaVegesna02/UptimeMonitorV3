const LABEL_TAIL_LENGTH = 4

/**
 * Shortens a probe-location id (e.g.
 * `SYNTHETIC_LOCATION-0000000000000060`, the real shape from
 * `ObservationDTO.location`) to an ellipsis-prefixed tail (`…0060`) — the
 * same presentation the approved prototype uses (STORY-122 AC3/AC5).
 */
export function locationLabel(location: string): string {
  if (location.length <= LABEL_TAIL_LENGTH) {
    return location
  }
  return `…${location.slice(-LABEL_TAIL_LENGTH)}`
}
