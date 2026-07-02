/**
 * The single swap-point for operator identity on decision POSTs
 * (STORY-015c). Auth is deferred to STORY-017, so every
 * `POST /api/v1/decisions/{proposal_id}` is attributed to this fixed
 * placeholder for now. When STORY-017 lands real operator identity
 * (session/JWT), only this function's implementation changes — no other
 * call site holds or duplicates the placeholder value.
 */
export function getActor(): string {
  return 'dashboard-operator'
}
