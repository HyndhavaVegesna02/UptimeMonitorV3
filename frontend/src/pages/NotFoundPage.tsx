import { Link } from 'react-router-dom'
import { EmptyState, Panel } from '../components'

/**
 * Catch-all for unknown routes (STORY-041 AC4) — keeps the Nav shell and
 * page chrome consistent instead of rendering an empty `<main>` for a
 * mistyped or stale URL.
 */
export function NotFoundPage() {
  return (
    <Panel title="Not found" headingLevel="h1">
      <EmptyState
        message="This page doesn't exist"
        detail="Check the URL, or go back to the Dashboard."
      />
      <Link to="/">Back to Dashboard</Link>
    </Panel>
  )
}
