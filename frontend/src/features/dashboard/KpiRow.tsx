import { ClipboardText, Gauge, Stack, Timer } from '@phosphor-icons/react'
import { formatLatency, formatPercent } from '../../lib/format'
import { Sparkline } from '../../components/Sparkline/Sparkline'
import { SummaryCard } from '../../components/SummaryCard/SummaryCard'
import { approvalsTone, componentsHealthTone } from './deriveKpiTone'
import { KpiMeter } from './KpiMeter'
import './KpiRow.css'

export interface KpiRowProps {
  /** `AvailabilityDTO.availability_pct` for the primary signal — a 0-1
   * fraction, `null` for a degenerate (no-data) window. */
  availabilityPct: number | null
  /** Per-check pass/fail proxy series, oldest-first (`healthSeries`). */
  availabilityTrend: number[]
  /** The count of distinct real `location` values seen across the fetched
   * history window (`DashboardPage.tsx`'s `new Set(...).size` over
   * `combinedHistory`) — real, not invented; not `AvailabilityDTO`'s own
   * `distinct_locations` field (the two are equal today with one signal,
   * but this prop's actual source is the history-derived set). */
  distinctLocations: number
  avgLatencyMs: number | null
  /** Latency series, oldest-first (`latencySeries`). */
  latencyTrend: number[]
  componentsHealthy: number
  componentsTotal: number
  componentsBreakdown: string | null
  pendingApprovals: number
}

/**
 * The Dashboard's KPI row (STORY-122 AC1): overall availability, avg
 * response time, components healthy, and pending approvals — every value
 * derived from real API data, never invented. Deltas are DELIBERATELY
 * omitted: no prior-period baseline is fetched by this story, and
 * fabricating one would violate "never invent a number" (web-interface-
 * guidelines) more than an absent delta pill costs in polish.
 *
 * Every one of the 4 cards carries a footer visual (STORY-138 AC3/AC4): the
 * two cards with a real time series (availability, response time) get a
 * `Sparkline`; the two without one (components healthy, pending approvals)
 * get a `KpiMeter` — same footprint, colored by the SAME rule-driven tone
 * vocabulary (`deriveKpiTone.ts`), so no card is left looking emptier than
 * its siblings and the accent coloring is deliberate, never an accidental
 * green/blue/none mix.
 */
export function KpiRow({
  availabilityPct,
  availabilityTrend,
  distinctLocations,
  avgLatencyMs,
  latencyTrend,
  componentsHealthy,
  componentsTotal,
  componentsBreakdown,
  pendingApprovals,
}: KpiRowProps) {
  return (
    <section className="kpi-row stagger" aria-label="Key metrics">
      <SummaryCard
        icon={Gauge}
        label="Overall availability · 24h"
        value={formatPercent(availabilityPct)}
        unit="%"
        sub={`Across ${distinctLocations} probe location${distinctLocations === 1 ? '' : 's'}`}
      >
        <Sparkline data={availabilityTrend} tone="positive" />
      </SummaryCard>

      <SummaryCard
        icon={Timer}
        label="Avg response time · 24h"
        value={formatLatency(avgLatencyMs)}
        unit="ms"
      >
        <Sparkline data={latencyTrend} tone="accent" />
      </SummaryCard>

      <SummaryCard
        icon={Stack}
        label="Components healthy"
        value={componentsHealthy}
        unit={`/ ${componentsTotal}`}
        sub={componentsBreakdown ?? 'All components healthy'}
      >
        <KpiMeter
          ratio={componentsTotal > 0 ? componentsHealthy / componentsTotal : 0}
          tone={componentsHealthTone(componentsHealthy, componentsTotal)}
        />
      </SummaryCard>

      <SummaryCard
        icon={ClipboardText}
        label="Pending approvals"
        value={pendingApprovals}
        href="/approvals"
        attention={pendingApprovals > 0}
        sub={pendingApprovals > 0 ? 'Review needed' : 'Nothing awaiting review'}
      >
        <KpiMeter ratio={1} tone={approvalsTone(pendingApprovals)} />
      </SummaryCard>
    </section>
  )
}
