import { ChartLineUp, MagnifyingGlass, ShieldCheck } from '@phosphor-icons/react'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { Sparkline } from '../../components/Sparkline/Sparkline'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { SummaryCard } from '../../components/SummaryCard/SummaryCard'
import { StyleguideSection } from './StyleguideSection'
import './StyleguidePage.css'

const HEALTH_STATUSES: HealthStatus[] = [
  'up',
  'degraded',
  'partial',
  'down',
  'maintenance',
  'unknown',
  'missing',
]

const AVAILABILITY_SERIES = [99.7, 99.8, 99.75, 99.9, 99.85, 99.95, 99.87]

/**
 * The design-system gallery (STORY-120 AC6) — every primitive, in every
 * state, in one place. This is the reviewable source of truth for the
 * visual language; downstream pages (STORY-121/122) compose these same
 * primitives rather than re-implementing them.
 */
export function StyleguidePage() {
  return (
    <div className="styleguide">
      <h1>Design system</h1>
      <p className="styleguide__intro">
        Every primitive, in every state — the single source of truth for the
        Uptime Monitor visual language.
      </p>

      <StyleguideSection title="Icon">
        <div className="styleguide-row">
          <Icon icon={ChartLineUp} aria-hidden />
          <Icon icon={ShieldCheck} aria-hidden size={24} weight="bold" />
          <Icon icon={MagnifyingGlass} label="Search" />
        </div>
      </StyleguideSection>

      <StyleguideSection title="Button">
        <div className="styleguide-row">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button disabled>Disabled</Button>
          <Button iconOnly aria-label="Search">
            <Icon icon={MagnifyingGlass} aria-hidden />
          </Button>
        </div>
      </StyleguideSection>

      <StyleguideSection title="Panel">
        <div className="styleguide-row styleguide-row--stack">
          <Panel title="Static panel">Plain surface — no hover affordance.</Panel>
          <Panel title="Interactive panel" interactive>
            Hover-lifts on fine-pointer devices (reduced-motion guarded).
          </Panel>
        </div>
      </StyleguideSection>

      <StyleguideSection title="StatusBadge">
        <div className="styleguide-row">
          {HEALTH_STATUSES.map((status) => (
            <StatusBadge key={status} status={status} />
          ))}
        </div>
      </StyleguideSection>

      <StyleguideSection title="SummaryCard">
        <div className="styleguide-grid">
          <SummaryCard
            icon={ChartLineUp}
            label="Overall availability · 24h"
            value="99.87"
            unit="%"
            delta={{ text: '0.04%', sentiment: 'positive' }}
            sub="Across 2 probe locations"
          >
            <Sparkline data={AVAILABILITY_SERIES} tone="positive" />
          </SummaryCard>
          <SummaryCard
            icon={ShieldCheck}
            label="Pending approvals"
            value="1"
            sub="Checkout Flow → Degraded"
            attention
            href="/approvals"
          />
        </div>
      </StyleguideSection>

      <StyleguideSection title="Sparkline">
        <div className="styleguide-row styleguide-row--sparkline">
          <Sparkline data={AVAILABILITY_SERIES} />
          <Sparkline data={[5, 5, 5, 5, 5]} tone="negative" />
        </div>
      </StyleguideSection>

      <StyleguideSection title="Loading / Error / Empty states">
        <div className="styleguide-row styleguide-row--stack">
          <LoadingState />
          <ErrorState />
          <ErrorState message="Could not load components" onRetry={() => undefined} />
          <EmptyState message="No components yet" detail="Add one to get started." />
        </div>
      </StyleguideSection>
    </div>
  )
}
