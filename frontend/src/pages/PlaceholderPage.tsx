import { Tile } from '../components'

export interface PlaceholderPageProps {
  title: string
}

/**
 * A minimal per-route placeholder (STORY-103 AC5 — "a minimal AppShell
 * placeholder using the new tokens is acceptable this story", the real
 * per-tab content is rewritten in the following per-page stories,
 * sprint-56+). One `<h1>` per route (a11y floor), rendered inside a
 * `Tile` so every route already sits on the new Mission Teal tokens.
 */
export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <Tile elevation="md">
      <h1>{title}</h1>
      <p>Rewrite in progress — this tab is being rebuilt on the new design system.</p>
    </Tile>
  )
}
