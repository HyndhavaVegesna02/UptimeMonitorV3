export function deriveMaintenanceStatus(
  startsAtIso: string,
  endsAtIso: string,
  now = new Date(),
): 'upcoming' | 'active' | 'past' {
  const start = new Date(startsAtIso).getTime()
  const end = new Date(endsAtIso).getTime()
  const current = now.getTime()

  if (current < start) {
    return 'upcoming'
  }
  if (current >= start && current < end) {
    return 'active'
  }
  return 'past'
}
