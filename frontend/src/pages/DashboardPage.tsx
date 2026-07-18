import { useMemo } from 'react'
import type { ComponentDTO, ComponentTopologyDTO } from '../api/types'
import { toHealthStatus } from '../api/statusMapping'
import {
  EmptyState,
  ErrorState,
  LatencySpark,
  LoadingState,
  RelativeTime,
  StatusBadge,
  Tile,
  UptimeBar,
} from '../components'
import type { HealthStatus } from '../components'
import { cx } from '../lib/cx'
import { formatLocationLabel } from '../lib/formatLocation'
import { formatPct } from '../features/availability/format'
import type { AvailabilityRange } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import { useComponents } from '../features/dashboard/useComponents'
import type { ComponentsFetchState } from '../features/dashboard/useComponents'
import type { ComponentUptime } from '../features/dashboard/useComponentUptime'
import { useComponentUptime } from '../features/dashboard/useComponentUptime'
import { useTopology } from '../features/dashboard/useTopology'
import { useMaintenanceWindows } from '../features/dashboard/useMaintenanceWindows'
import type { MaintenanceWindowsFetchState } from '../features/dashboard/useMaintenanceWindows'
import { countActiveOrUpcomingWindows } from '../features/dashboard/maintenanceSummary'
import { useApprovalsBadge } from '../features/shell/useApprovalsBadge'
import { deriveOverallStatus } from '../features/shell/deriveOverallStatus'
import { observationHealth } from '../features/history/observationHealth'
import { useAllHistory } from '../features/history/useAllHistory'
import type { UseAllHistoryResult } from '../features/history/useAllHistory'
import './DashboardPage.css'

/** Stable empty reference (mirrors the pre-rewrite Dashboard's convention) —
 * reused instead of a fresh `[]` literal per render so `useComponentUptime`'s
 * `[topology, range]`-keyed fetcher doesn't see a "changed" dependency on
 * every render while topology hasn't loaded yet. */
const EMPTY_TOPOLOGY: ComponentTopologyDTO[] = []

/** The most rows the recent-checks feed tile ever renders (STORY-105, design
 * brief §IA — "live recent checks feed tile"). */
const RECENT_CHECKS_LIMIT = 8

/** A fixed 24h window for the Dashboard's uptime/latency data (there is no
 * window selector on this tab — that is Availability's job); memoized once
 * so `useComponentUptime`/`useAllHistory`'s fetchers keep a stable identity
 * across re-renders (mirrors the pre-rewrite Dashboard's `useDashboardRange`
 * convention). */
function useDashboardRange(): AvailabilityRange {
  return useMemo(() => windowToRange('24h'), [])
}

/** The big hero-tile KPI word, matching `StatusBadge`'s own label text
 * exactly (a page-local copy — this file's own convention, mirroring the
 * pre-rewrite Dashboard's `formatLatency` "Wave-2 file-scope isolation"
 * precedent — rather than exporting `StatusBadge`'s private label map). */
const HERO_STATUS_LABELS: Record<HealthStatus, string> = {
  up: 'Up',
  down: 'Down',
  degraded: 'Degraded',
  partial: 'Partial outage',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  missing: 'Missing data',
}

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — never `0 ms` (mirrors the pre-rewrite Dashboard's
 * own `formatLatency`, kept as this page's own copy per that same
 * file-scope-isolation convention). */
function formatLatency(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

interface HeroTileProps {
  state: ComponentsFetchState
  retry: () => void
}

/**
 * The hero "system status" tile (STORY-105 AC2, design brief §IA — "hero
 * system-status tile (overall state, worst-of, big type)"): the current
 * overall status as a large KPI word (the ui-ux-pro-max "current value as
 * large visible text" pattern) alongside a `StatusBadge` (status is never
 * color-only) and an honest "N of M components operational" subline. An
 * empty component list renders `deriveOverallStatus`'s own explicit
 * `'unknown'` — never a fabricated "all up".
 */
function HeroTile({ state, retry }: HeroTileProps) {
  if (state.phase === 'loading') {
    return (
      <Tile elevation="lg" className="dashboard-grid__hero">
        <LoadingState label="Loading system status…" />
      </Tile>
    )
  }

  if (state.phase === 'error') {
    return (
      <Tile elevation="lg" className="dashboard-grid__hero">
        <ErrorState message="Could not load system status" onRetry={retry} />
      </Tile>
    )
  }

  const components = state.data
  const overallStatus = deriveOverallStatus(components)
  const upCount = components.filter((component) => toHealthStatus(component.status) === 'up')
    .length

  return (
    <Tile elevation="lg" accent={overallStatus} className="dashboard-grid__hero">
      <span className="text-label dashboard-grid__hero-label">System status</span>
      <p className="dashboard-grid__hero-kpi">{HERO_STATUS_LABELS[overallStatus]}</p>
      <StatusBadge status={overallStatus} />
      <p className="text-caption dashboard-grid__hero-sub">
        {components.length === 0
          ? 'No components configured'
          : `${upCount} of ${components.length} component${
              components.length === 1 ? '' : 's'
            } operational`}
      </p>
    </Tile>
  )
}

interface ComponentTileProps {
  component: ComponentDTO
  topologyEntry: ComponentTopologyDTO | undefined
  uptime: ComponentUptime | undefined
}

/**
 * One per-component tile (STORY-105 AC2/AC3, design brief §IA — "per-
 * component tiles (uptime bar + latency spark + status)"): name + status +
 * uptime bar + inline latency spark + "Last observed" `RelativeTime`, the
 * whole tile a drill-through link to Check History filtered to this
 * component's primary signal. A component with no topology signals yet
 * (topology still loading, or genuinely zero signals) renders the SAME
 * content as a plain, non-interactive tile rather than a broken link —
 * graceful degradation, mirroring the pre-rewrite Dashboard's convention.
 */
function ComponentTile({ component, topologyEntry, uptime }: ComponentTileProps) {
  const health = toHealthStatus(component.status)
  const primarySignal = topologyEntry?.signals[0]
  const segments = uptime?.segments ?? []
  const pct = uptime?.pct ?? null
  const latencyPoints = uptime?.latencyPoints ?? []
  const lastObservedIso = uptime?.lastObservedIso ?? null

  const content = (
    <>
      <div className="dashboard-grid__component-header">
        <span className="text-body-lg dashboard-grid__component-name">{component.name}</span>
        <StatusBadge status={health} />
      </div>
      <UptimeBar
        segments={segments}
        label={`${component.name} uptime`}
        className="dashboard-grid__component-uptime"
      />
      <div className="dashboard-grid__component-metrics">
        <span className="text-mono dashboard-grid__component-pct">{formatPct(pct)}</span>
        <LatencySpark
          points={latencyPoints}
          label={`${component.name} latency`}
          className="dashboard-grid__component-spark"
        />
      </div>
      <p className="text-caption dashboard-grid__component-observed">
        {lastObservedIso ? (
          <>
            Last observed <RelativeTime iso={lastObservedIso} />
          </>
        ) : (
          'No recent checks'
        )}
      </p>
    </>
  )

  if (primarySignal) {
    return (
      <Tile
        elevation="md"
        accent={health}
        href={`/check-history?signal=${encodeURIComponent(primarySignal.signal_key)}`}
        className="dashboard-grid__component"
      >
        {content}
      </Tile>
    )
  }

  return (
    <Tile elevation="md" accent={health} interactive={false} className="dashboard-grid__component">
      {content}
    </Tile>
  )
}

interface ActionTileProps {
  label: string
  count: number | undefined
  sublabel: string
  href: string
  loadingLabel: string
  variantClassName: string
}

/**
 * A pending-count action tile (STORY-105 AC2, design brief §IA — "action
 * tiles (pending approvals / maintenance — neutral at zero, accented when
 * >0)"): a whole-tile link (never a button styled to look like a link) to
 * the relevant tab, with the count and its sublabel always VISIBLE text —
 * the accent edge is a reinforcing cue, never the sole one. `count ===
 * undefined` (loading, or the underlying hook's own graceful-degradation
 * "no signal" case) renders a loading skeleton rather than a fabricated 0.
 */
function ActionTile({
  label,
  count,
  sublabel,
  href,
  loadingLabel,
  variantClassName,
}: ActionTileProps) {
  if (count === undefined) {
    return (
      <Tile elevation="md" className={cx('dashboard-grid__action', variantClassName)}>
        <LoadingState label={loadingLabel} />
      </Tile>
    )
  }

  return (
    <Tile
      elevation="md"
      href={href}
      className={cx(
        'dashboard-grid__action',
        variantClassName,
        count > 0 && 'dashboard-grid__action--active',
      )}
    >
      <span className="text-label dashboard-grid__action-label">{label}</span>
      <span className="text-mono dashboard-grid__action-value">{count}</span>
      <span className="text-caption dashboard-grid__action-sub">{sublabel}</span>
    </Tile>
  )
}

interface MaintenanceActionTileProps {
  state: MaintenanceWindowsFetchState
  retry: () => void
}

/** The maintenance action tile's own loading/error/success branching
 * (STORY-105 AC2, AC4) — distinct from `ActionTile`'s undefined-collapses-
 * loading-and-error shape because `useMaintenanceWindows` exposes a full
 * `FetchState`, so this tile CAN show a genuine error+retry affordance. */
function MaintenanceActionTile({ state, retry }: MaintenanceActionTileProps) {
  if (state.phase === 'loading') {
    return (
      <Tile
        elevation="md"
        className="dashboard-grid__action dashboard-grid__action--maintenance"
      >
        <LoadingState label="Loading maintenance…" />
      </Tile>
    )
  }

  if (state.phase === 'error') {
    return (
      <Tile
        elevation="md"
        className="dashboard-grid__action dashboard-grid__action--maintenance"
      >
        <ErrorState message="Could not load maintenance" onRetry={retry} />
      </Tile>
    )
  }

  const count = countActiveOrUpcomingWindows(state.data)

  return (
    <Tile
      elevation="md"
      href="/maintenance"
      className={cx(
        'dashboard-grid__action',
        'dashboard-grid__action--maintenance',
        count > 0 && 'dashboard-grid__action--active',
      )}
    >
      <span className="text-label dashboard-grid__action-label">Maintenance</span>
      <span className="text-mono dashboard-grid__action-value">{count}</span>
      <span className="text-caption dashboard-grid__action-sub">active or upcoming</span>
    </Tile>
  )
}

interface FeedTileProps {
  state: UseAllHistoryResult['state']
  retry: () => void
}

/**
 * The "recent checks" feed tile (STORY-105 AC3, design brief §IA — "live
 * recent checks feed tile"): the latest `RECENT_CHECKS_LIMIT` observations
 * system-wide (newest-first, `useAllHistory`'s own merge across every
 * signal), each row a `StatusBadge` + component name + a SHORT location
 * label (`formatLocationLabel` — never the raw vendor id) + latency +
 * `RelativeTime` (never a raw ISO string as visible text).
 */
function FeedTile({ state, retry }: FeedTileProps) {
  return (
    <Tile elevation="md" className="dashboard-grid__feed">
      <h2 className="text-label dashboard-grid__feed-title">Recent checks</h2>

      {state.phase === 'loading' && <LoadingState label="Loading recent checks…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load recent checks" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.length === 0 && (
        <EmptyState message="No checks recorded yet" />
      )}

      {state.phase === 'success' && state.data.length > 0 && (
        <ul className="dashboard-grid__feed-list">
          {state.data.slice(0, RECENT_CHECKS_LIMIT).map((row) => (
            <li
              key={`${row.signal_key}::${row.location}::${row.observed_at}`}
              className="dashboard-grid__feed-item"
            >
              <StatusBadge status={observationHealth(row.health)} />
              <span className="text-body dashboard-grid__feed-name">{row.componentName}</span>
              <span className="text-caption dashboard-grid__feed-location">
                {formatLocationLabel(row.location)}
              </span>
              <span className="text-mono dashboard-grid__feed-latency">
                {formatLatency(row.latency_ms)}
              </span>
              <RelativeTime iso={row.observed_at} className="text-caption dashboard-grid__feed-time" />
            </li>
          ))}
        </ul>
      )}
    </Tile>
  )
}

/**
 * The bento-grid mission-control Dashboard (STORY-105, design brief §IA —
 * "one page = one decision: is anything wrong, and where"): a hero
 * system-status tile, one tile per monitored component, two action tiles
 * (pending approvals / maintenance), and a recent-checks feed tile — an
 * asymmetric CSS grid (`DashboardPage.css`) that stacks cleanly at every
 * first-class breakpoint (AC1).
 *
 * Every tile's data comes from an INDEPENDENT fetch (AC4): `useComponents`
 * (the primary fetch the hero tile + per-component tiles need),
 * `useTopology` (an enhancement — per-component signal/uptime linkage),
 * `useComponentUptime` (per-component pct/segments/latency, itself never
 * rejecting), `useApprovalsBadge`/`useMaintenanceWindows` (the two action
 * tiles), and `useAllHistory` (the feed tile). A failure in any ONE of them
 * renders that tile's own error state and never blanks any other tile.
 */
export function DashboardPage() {
  const componentsResult = useComponents()
  const topologyResult = useTopology()
  const maintenanceResult = useMaintenanceWindows()
  const approvalsCount = useApprovalsBadge()
  const range = useDashboardRange()

  const topology =
    topologyResult.state.phase === 'success' ? topologyResult.state.data : EMPTY_TOPOLOGY
  const { state: uptimeState } = useComponentUptime(topology, range)
  const { state: historyState, retry: retryHistory } = useAllHistory(range)

  const topologyById = useMemo(() => {
    const map = new Map<string, ComponentTopologyDTO>()
    for (const entry of topology) {
      map.set(entry.id, entry)
    }
    return map
  }, [topology])

  const uptimeByComponentId = uptimeState.phase === 'success' ? uptimeState.data : {}
  const components = componentsResult.state.phase === 'success' ? componentsResult.state.data : []

  return (
    <div className="dashboard-page">
      <div className="dashboard-page__header">
        <h1 className="text-h1 dashboard-page__title">Dashboard</h1>
        <p className="text-caption dashboard-page__subtitle">
          Mission-control view of every monitored component
        </p>
      </div>

      <div className="dashboard-grid">
        <HeroTile state={componentsResult.state} retry={componentsResult.retry} />

        {componentsResult.state.phase === 'success' && components.length === 0 && (
          <Tile elevation="md" className="dashboard-grid__empty">
            <EmptyState message="No components configured" />
          </Tile>
        )}

        {componentsResult.state.phase === 'success' &&
          components.map((component) => (
            <ComponentTile
              key={component.id}
              component={component}
              topologyEntry={topologyById.get(component.id)}
              uptime={uptimeByComponentId[component.id]}
            />
          ))}

        <ActionTile
          label="Pending approvals"
          count={approvalsCount}
          sublabel="open"
          href="/approvals"
          loadingLabel="Loading pending approvals…"
          variantClassName="dashboard-grid__action--approvals"
        />
        <MaintenanceActionTile state={maintenanceResult.state} retry={maintenanceResult.retry} />
        <FeedTile state={historyState} retry={retryHistory} />
      </div>
    </div>
  )
}
