/**
 * The single swap-point for operator identity on decision POSTs
 * (STORY-015c). Real operator identity is unassigned (no story queued), so
 * every `POST /api/v1/decisions/{proposal_id}` is attributed to this fixed
 * placeholder for now. When operator identity is implemented (session/JWT),
 * only this function's implementation changes — no other call site holds or
 * duplicates the placeholder value.
 */
export function getActor(): string {
  return 'dashboard-operator'
}
