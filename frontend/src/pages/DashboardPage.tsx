import { ComponentsProbe } from '../features/dashboard/ComponentsProbe'
import { Panel } from '../components'

/**
 * Placeholder — the real Dashboard content ships in STORY-015b. Hosts the
 * AC3 proving example (typed API client end to end against
 * GET /api/v1/components) so the scaffold demonstrates real connectivity.
 */
export function DashboardPage() {
  return (
    <Panel title="Dashboard" headingLevel="h1">
      <p className="text-body">Live health overview lands in STORY-015b.</p>
      <h2 className="text-h2">Backend connectivity check</h2>
      <ComponentsProbe />
    </Panel>
  )
}
