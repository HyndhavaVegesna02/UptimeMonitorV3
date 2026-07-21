import { Panel } from '../Panel/Panel'
import './PlaceholderPage.css'

export interface PlaceholderPageProps {
  description: string
}

/**
 * Minimal per-tab placeholder (STORY-121) — Availability/History/Approvals/
 * Maintenance/Publications (and Dashboard, until STORY-122 fills it with
 * real content) all render one of these. A single shared component so the
 * near-identical pages don't each re-implement the same shape (checklist:
 * N same-shape variants share one assembly helper).
 *
 * No `title`/heading here deliberately: `ShellLayout`'s topbar already
 * renders the page's single `<h1>` (the active tab's label) — a placeholder
 * repeating it would create a second top-level heading.
 */
export function PlaceholderPage({ description }: PlaceholderPageProps) {
  return (
    <Panel>
      <p className="placeholder-page__description">{description}</p>
      <p className="placeholder-page__note">Coming soon.</p>
    </Panel>
  )
}
