import { Fragment, useMemo, useState } from 'react'
import type { ComponentDTO, ComponentTopologyDTO, MaintenanceWindowDTO, TopologySignalDTO } from '../api/types'
import { toHealthStatus } from '../api/statusMapping'
import {
  EmptyState,
  ErrorState,
  Icon,
  LoadingState,
  PageHeader,
  Panel,
  RelativeTime,
  StatusBadge,
  SummaryCard,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  UptimeBar,
} from '../components'
import { cx } from '../lib/cx'
import { formatPct } from '../features/availability/format'
import { formatLocationLabel } from '../lib/formatLocation'
import type { AvailabilityRange } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import { actionCardView } from '../features/dashboard/actionCard'
import { countActiveOrUpcomingWindows } from '../features/dashboard/maintenanceSummary'
import { summarizeComponents } from '../features/dashboard/summary'
import { useComponents } from '../features/dashboard/useComponents'
import { useComponentSignals } from '../features/dashboard/useComponentSignals'
import type { ComponentUptime } from '../features/dashboard/useComponentUptime'
import { useComponentUptime } from '../features/dashboard/useComponentUptime'
import { useMaintenanceWindows } from '../features/dashboard/useMaintenanceWindows'
import { useTopology } from '../features/dashboard/useTopology'
import { useApprovalsBadge } from '../features/shell/useApprovalsBadge'
import { deriveWindowState } from '../features/maintenance/windowState'
import './DashboardPage.css'

/** Stable empty references (STORY-057) — reused instead of a fresh `[]`
 * literal per render so hooks keyed on these (`useComponentUptime`'s
 * `[topology, range]`, `useComponentSignals`'s `[signals, range]`) don't see
 * a "changed" dependency on every render while their real data hasn't
 * loaded yet. */
const EMPTY_TOPOLOGY: ComponentTopologyDTO[] = []
const EMPTY_SIGNALS: TopologySignalDTO[] = []
const EMPTY_MAINTENANCE_WINDOWS: MaintenanceWindowDTO[] = []

/** A fixed 24h window for the Dashboard's uptime sparkline/rollup (STORY-057
 * AC3) — there is no window selector on this tab (that's Availability's
 * job); memoized once so `useComponentUptime`'s fetcher keeps a stable
 * identity across re-renders. */
function useDashboardRange(): AvailabilityRange {
  return useMemo(() => windowToRange('24h'), [])
}

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — NEVER `0 ms` (mirrors
 * `CheckHistoryPage.tsx::formatLatency`, kept as this page's own copy per
 * the sprint-38 Wave-2 file-scope isolation rule). */
function formatLatency(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

/**
 * True iff ANY of `windows` belonging to `componentId` is currently ACTIVE
 * per the half-open `deriveWindowState` rule (STORY-046, dossier §6/§11 —
 * health and maintenance are separate concepts, so this never touches
 * `toHealthStatus`/`ComponentStatus`). Multiple windows on one component are
 * OR'd together: any single active window is enough to mark it.
 */
function isUnderActiveMaintenance(
  componentId: string,
  windows: MaintenanceWindowDTO[],
): boolean {
  return windows
    .filter((window) => window.component_id === componentId)
    .some((window) => deriveWindowState(window.starts_at, window.ends_at) === 'active')
}

interface SignalsDrilldownProps {
  id: string
  signals: TopologySignalDTO[]
  range: AvailabilityRange
  colSpan: number
}

/**
 * The expanded-row signal drill-down (STORY-057 AC2) — mounted ONLY while
 * its parent row is expanded, so `useComponentSignals`'s fetch (one
 * `getHistory` call per signal) never fires for a collapsed component. A
 * failure here is scoped to this region alone (its own `ErrorState`) —
 * it never blocks or clears the primary components table above it.
 */
function SignalsDrilldown({ id, signals, range, colSpan }: SignalsDrilldownProps) {
  const { state, retry } = useComponentSignals(signals, range)

  return (
    <TableRow id={id} className="dashboard-page__drilldown-row">
      <TableCell colSpan={colSpan} className="dashboard-page__drilldown-cell">
        <div className="dashboard-page__drilldown-label text-caption">
          Signals feeding this component
        </div>
        {state.phase === 'loading' && <LoadingState label="Loading signals…" />}
        {state.phase === 'error' && (
          <ErrorState message="Could not load signals" onRetry={retry} />
        )}
        {state.phase === 'success' && state.data.length === 0 && (
          <EmptyState message="No signals for this component" />
        )}
        {state.phase === 'success' && state.data.length > 0 && (
          <Table className="dashboard-page__signals-table">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Signal</TableHeaderCell>
                <TableHeaderCell>Location</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Latency</TableHeaderCell>
                <TableHeaderCell>Last observed</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {state.data.map((row) => (
                <TableRow key={row.key}>
                  <TableCell>{row.label}</TableCell>
                  <TableCell className="text-mono" title={row.location ?? undefined}>
                    {row.location === null ? '—' : formatLocationLabel(row.location)}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={row.status} />
                  </TableCell>
                  <TableCell className="text-mono">{formatLatency(row.latencyMs)}</TableCell>
                  <TableCell className="text-mono">
                    {row.lastObserved === null ? '—' : <RelativeTime iso={row.lastObserved} />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </TableCell>
    </TableRow>
  )
}

interface ComponentRowProps {
  component: ComponentDTO
  signals: TopologySignalDTO[]
  canExpand: boolean
  expanded: boolean
  onToggle: () => void
  uptime: ComponentUptime | undefined
  underMaintenance: boolean
  range: AvailabilityRange
}

/** One component row (STORY-057 AC2/AC3): chevron + status dot + mono name
 * (expandable when the component has topology signals to drill into) +
 * `UptimeBar` sparkline + uptime % + status pill. The status DOT next to the
 * name is decorative (`aria-hidden`) — the accessible health label lives in
 * the `StatusBadge` at the row's end, so status is never color-only. */
function ComponentRow({
  component,
  signals,
  canExpand,
  expanded,
  onToggle,
  uptime,
  underMaintenance,
  range,
}: ComponentRowProps) {
  const health = toHealthStatus(component.status)
  const segments = uptime?.segments ?? []
  const pct = uptime?.pct ?? null

  const nameContent = (
    <>
      <span
        className={cx('dashboard-page__dot', `dashboard-page__dot--${health}`)}
        aria-hidden="true"
      />
      <span className="text-mono dashboard-page__name">{component.name}</span>
    </>
  )

  return (
    <Fragment>
      <TableRow>
        <TableCell>
          {canExpand ? (
            <button
              type="button"
              className="dashboard-page__expand"
              aria-expanded={expanded}
              aria-controls={`drilldown-${component.id}`}
              onClick={onToggle}
            >
              <Icon
                name="chevron-right"
                className={cx(
                  'dashboard-page__chevron',
                  expanded && 'dashboard-page__chevron--expanded',
                )}
              />
              {nameContent}
            </button>
          ) : (
            <span className="dashboard-page__name-static">{nameContent}</span>
          )}
        </TableCell>
        <TableCell>
          <div className="dashboard-page__uptime">
            <UptimeBar
              segments={segments}
              label={`${component.name} uptime`}
              className="dashboard-page__uptime-bar"
            />
            <span className="text-mono dashboard-page__uptime-pct">{formatPct(pct)}</span>
          </div>
        </TableCell>
        <TableCell>
          <div className="dashboard-page__status-cell">
            <StatusBadge status={health} />
            {underMaintenance && (
              <StatusBadge status="maintenance" label="Under maintenance" />
            )}
          </div>
        </TableCell>
      </TableRow>
      {expanded && canExpand && (
        <SignalsDrilldown id={`drilldown-${component.id}`} signals={signals} range={range} colSpan={3} />
      )}
    </Fragment>
  )
}

/**
 * The Dashboard tab (STORY-057 rebuild of STORY-015b/STORY-046, re-scoped by
 * STORY-099): a summary row of `SummaryCard`s (AC1) above every monitored
 * component's health, uptime sparkline, and status — grouped under ONE
 * section (no `group` field on the wire yet; per-group sections are
 * STORY-067). Fetches `GET /api/v1/components` (`useComponents`, the
 * primary/blocking fetch — its own loading/error/empty states gate the whole
 * table; STORY-099 also reads its `lastUpdatedAt` for the header's "Updated
 * Xs ago" indicator), `GET /api/v1/topology` (`useTopology`, feeds the expand
 * affordance + signal drill-down + uptime's primary-signal history),
 * `GET /api/v1/approvals` (`useApprovalsBadge`, the "Pending approvals"
 * cross-tab awareness card — STORY-099 AC2), and `GET /api/v1/maintenance`
 * (`useMaintenanceWindows`, both the STORY-046 per-row overlay AND the
 * "Maintenance" awareness card's active/upcoming count).
 *
 * Graceful degradation (AC2): topology/uptime/maintenance are all
 * ENHANCEMENTS layered on top of the primary components list — a failure or
 * loading state in any of them degrades to "no expand affordance" / "no
 * uptime data" / "no maintenance badge" respectively, and NEVER blocks or
 * clears the primary table. Only a `useComponents` failure blocks the page.
 * The two action cards degrade the same way, via `actionCardView` — an
 * unresolved count renders an honest em-dash, never a fabricated 0.
 *
 * The header's "Updated Xs ago" indicator (STORY-099 AC3) reads
 * `useComponents`' own `lastUpdatedAt` and renders it through the shared
 * `RelativeTime` (STORY-098) — it is hidden entirely before the first
 * successful load rather than showing a fabricated/placeholder instant.
 */
export function DashboardPage() {
  const { state, retry, lastUpdatedAt } = useComponents()
  const { state: topologyState } = useTopology()
  const { state: maintenanceState } = useMaintenanceWindows()
  const approvalsCount = useApprovalsBadge()
  const range = useDashboardRange()

  const topology = topologyState.phase === 'success' ? topologyState.data : EMPTY_TOPOLOGY
  const { state: uptimeState } = useComponentUptime(topology, range)

  const [expandedIds, setExpandedIds] = useState<ReadonlySet<string>>(new Set())

  function toggleExpanded(componentId: string) {
    setExpandedIds((current) => {
      const next = new Set(current)
      if (next.has(componentId)) {
        next.delete(componentId)
      } else {
        next.add(componentId)
      }
      return next
    })
  }

  const topologyById = useMemo(() => {
    const map = new Map<string, ComponentTopologyDTO>()
    for (const entry of topology) {
      map.set(entry.id, entry)
    }
    return map
  }, [topology])

  const maintenanceWindows =
    maintenanceState.phase === 'success' ? maintenanceState.data : EMPTY_MAINTENANCE_WINDOWS
  const uptimeByComponentId = uptimeState.phase === 'success' ? uptimeState.data : {}

  const components = state.phase === 'success' ? state.data : []

  // Cross-tab awareness action cards (STORY-099 AC2): an unresolved count
  // (loading or error on either fetch) stays honestly unknown — `undefined`
  // — rather than fabricating a 0, mirroring `useApprovalsBadge`'s own
  // graceful-degradation contract.
  const maintenanceCount =
    maintenanceState.phase === 'success'
      ? countActiveOrUpcomingWindows(maintenanceState.data)
      : undefined
  const approvalsCard = actionCardView(approvalsCount)
  const maintenanceCard = actionCardView(maintenanceCount)

  const headerActions =
    lastUpdatedAt !== null ? (
      <span className="dashboard-page__updated text-caption">
        Updated <RelativeTime iso={lastUpdatedAt} />
      </span>
    ) : undefined

  return (
    <div className="dashboard-page page page--wide">
      {/* Accessible name kept as "Dashboard" (not the mock's "System
          health") — `AppShell`/`App`'s routing tests assert every route's
          h1 matches its nav tab label, and those shell-level test files
          are out of scope for this story. */}
      <PageHeader
        title="Dashboard"
        subtitle={
          state.phase === 'success'
            ? `Live status across ${components.length} monitored component${
                components.length === 1 ? '' : 's'
              } · click a row to see its signals`
            : 'Live status across monitored components · click a row to see its signals'
        }
        actions={headerActions}
      />

      {state.phase === 'success' && (
        <div className="dashboard-page__summary">
          <SummaryCard
            label="Pending approvals"
            value={approvalsCard.value}
            sub="open"
            tone={approvalsCard.tone}
            href="/approvals"
          />
          <SummaryCard
            label="Maintenance"
            value={maintenanceCard.value}
            sub="active or upcoming"
            tone={maintenanceCard.tone}
            href="/maintenance"
          />
          {summarizeComponents(components).map((card) => (
            <SummaryCard
              key={card.key}
              label={card.label}
              value={card.value}
              sub={card.sub}
              tone={card.tone}
              neutralAtZero={card.neutralAtZero}
            />
          ))}
        </div>
      )}

      <Panel>
        {state.phase === 'loading' && <LoadingState label="Loading components…" />}

        {state.phase === 'error' && (
          <ErrorState message="Could not load components" onRetry={retry} />
        )}

        {state.phase === 'success' && components.length === 0 && (
          <EmptyState message="No components configured" />
        )}

        {state.phase === 'success' && components.length > 0 && (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Component</TableHeaderCell>
                <TableHeaderCell>Uptime</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {components.map((component) => {
                const topologyEntry = topologyById.get(component.id)
                const signals = topologyEntry?.signals ?? EMPTY_SIGNALS
                const canExpand = topologyState.phase === 'success' && signals.length > 0

                return (
                  <ComponentRow
                    key={component.id}
                    component={component}
                    signals={signals}
                    canExpand={canExpand}
                    expanded={expandedIds.has(component.id)}
                    onToggle={() => toggleExpanded(component.id)}
                    uptime={uptimeByComponentId[component.id]}
                    underMaintenance={isUnderActiveMaintenance(
                      component.id,
                      maintenanceWindows,
                    )}
                    range={range}
                  />
                )
              })}
            </TableBody>
          </Table>
        )}
      </Panel>
    </div>
  )
}
