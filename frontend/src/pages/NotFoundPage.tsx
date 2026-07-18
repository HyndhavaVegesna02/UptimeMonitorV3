import { Link } from 'react-router-dom'
import { Tile } from '../components'

/**
 * Catch-all for an unknown path (STORY-041 originally; re-skinned onto the
 * Mission Teal `Tile` primitive at STORY-103 — behavior unchanged: a
 * heading plus a link back to the Dashboard route).
 */
export function NotFoundPage() {
  return (
    <Tile elevation="md">
      <h1>Not found</h1>
      <p>That page doesn&apos;t exist.</p>
      <Link to="/">Back to Dashboard</Link>
    </Tile>
  )
}
