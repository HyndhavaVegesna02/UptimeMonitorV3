import type { ReactNode } from 'react'
import { getApprovals, getComponents, getMaintenance } from '../../api/client'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { ComponentsRoster } from '../../features/dashboard/ComponentsRoster'
import { KpiRow } from '../../features/dashboard/KpiRow'
import { MaintenancePanel } from '../../features/dashboard/MaintenancePanel'
import { ProbeLocationsPanel } from '../../features/dashboard/ProbeLocationsPanel'
import { RecentChecksFeed } from '../../features/dashboard/RecentChecksFeed'
import { ResponseTimeChart } from '../../features/dashboard/ResponseTimeChart'
import { deriveOverallAvailability, flattenHistory } from '../../features/dashboard/aggregateSignals'
import {
  averageLatencyMs,
  healthSeries,
  latencySeries,
  summarizeComponentsHealth,
} from '../../features/dashboard/deriveKpis'
import { describeComponentsHealthBreakdown } from '../../features/dashboard/describeComponentsHealthBreakdown'
import { deriveProbeLocations } from '../../features/dashboard/deriveProbeLocations'
import { deriveRecentChecks } from '../../features/dashboard/deriveRecentChecks'
import { deriveRoster } from '../../features/dashboard/deriveRoster'
import { useSignalsData } from '../../features/dashboard/useSignalsData'
import { combineFetchPhase, firstErrorMessage } from '../../lib/combineFetchStates'
import { useFetch } from '../../lib/useFetch'
import './DashboardPage.css'

const WINDOW_LABEL = 'last 24 hours'
const RECENT_CHECKS_LIMIT = 6

/** Renders the loading/error phase for a region, or `content()` once every
 * underlying fetch has succeeded (STORY-122 AC6 — every region has an
 * explicit loading/error state; a region's own EMPTY case is handled by
 * the content component itself, e.g. `ResponseTimeChart`'s own
 * `EmptyState` for a zero-observation window). A plain function, not a
 * component — called directly during render, no new component identity
 * per render (vercel-react-best-practices: no inline component defs). */
function renderRegion(
  phase: 'loading' | 'error' | 'success',
  errorMessage: string | undefined,
  onRetry: () => void,
  content: () => ReactNode,
): ReactNode {
  if (phase === 'loading') {
    return <LoadingState />
  }
  if (phase === 'error') {
    return <ErrorState message={errorMessage} onRetry={onRetry} />
  }
  return content()
}

/**
 * The Dashboard (STORY-122) — KPIs, a response-time chart, probe
 * locations, upcoming maintenance, recent checks, and the components
 * roster, all on REAL `/api/v1` data (no invented numbers). Fetches
 * components/approvals/maintenance in parallel (no waterfall); per-signal
 * history/availability is genuinely sequenced after components resolve
 * (there is no signal_key to query before then) via `useSignalsData`.
 *
 * No `<h1>` here — `ShellLayout`'s `Topbar` already renders the page's one
 * top-level heading (AC6); every panel below is a level-two heading via
 * the shared `Panel` primitive.
 */
export function DashboardPage() {
  const componentsFetch = useFetch(getComponents)
  const approvalsFetch = useFetch(getApprovals)
  const maintenanceFetch = useFetch(getMaintenance)
  const signalsState = useSignalsData(componentsFetch.state)

  // Fresh each render, like `ShellLayout`'s `now={new Date()}` — this is a
  // "what time is it right now" reference for relative-time formatting,
  // not a captured success timestamp (contrast `useFetch.succeededAt`).
  const now = new Date()

  const components = componentsFetch.state.phase === 'success' ? componentsFetch.state.data : []
  const approvals = approvalsFetch.state.phase === 'success' ? approvalsFetch.state.data : []
  const maintenanceWindows = maintenanceFetch.state.phase === 'success' ? maintenanceFetch.state.data : []
  const signalsData = signalsState.phase === 'success' ? signalsState.data : {}

  // Not memoized: `flattenHistory` is a cheap flatten+sort over a small
  // per-signal map (the real topology has a handful of signals, each with
  // a bounded `HISTORY_LIMIT`-capped observation list) — memoizing would
  // need `signalsData` itself to be a referentially-stable object across
  // the "not yet successful" renders, which it isn't (a fresh `{}` each
  // time), so the memo would never actually hit.
  const combinedHistory = flattenHistory(signalsData)

  const kpiPhase = combineFetchPhase([componentsFetch.state, approvalsFetch.state, signalsState])
  const kpiError = firstErrorMessage([componentsFetch.state, approvalsFetch.state, signalsState])
  const retryKpiRegion = () => {
    componentsFetch.retry()
    approvalsFetch.retry()
  }

  const signalsPhase = combineFetchPhase([componentsFetch.state, signalsState])
  const signalsError = firstErrorMessage([componentsFetch.state, signalsState])
  const retrySignalsRegion = () => componentsFetch.retry()

  const maintenancePhase = combineFetchPhase([maintenanceFetch.state])
  const maintenanceError = firstErrorMessage([maintenanceFetch.state])

  return (
    <div className="dashboard-page">
      {renderRegion(kpiPhase, kpiError, retryKpiRegion, () => {
        const { healthy, total } = summarizeComponentsHealth(components)
        return (
          <KpiRow
            availabilityPct={deriveOverallAvailability(signalsData)}
            availabilityTrend={healthSeries(combinedHistory)}
            distinctLocations={new Set(combinedHistory.map((observation) => observation.location)).size}
            avgLatencyMs={averageLatencyMs(combinedHistory)}
            latencyTrend={latencySeries(combinedHistory)}
            componentsHealthy={healthy}
            componentsTotal={total}
            componentsBreakdown={describeComponentsHealthBreakdown(components)}
            pendingApprovals={approvals.length}
          />
        )
      })}

      <div className="dashboard-page__content-grid">
        <div className="dashboard-page__col dashboard-page__col--main">
          <Panel title="Response time">
            {renderRegion(signalsPhase, signalsError, retrySignalsRegion, () => (
              <ResponseTimeChart observations={combinedHistory} windowLabel={WINDOW_LABEL} />
            ))}
          </Panel>
          {renderRegion(signalsPhase, signalsError, retrySignalsRegion, () => (
            <RecentChecksFeed rows={deriveRecentChecks(components, signalsData, now, RECENT_CHECKS_LIMIT)} />
          ))}
        </div>

        <div className="dashboard-page__col dashboard-page__col--side">
          {renderRegion(signalsPhase, signalsError, retrySignalsRegion, () => (
            <ProbeLocationsPanel locations={deriveProbeLocations(combinedHistory)} />
          ))}
          {renderRegion(maintenancePhase, maintenanceError, () => maintenanceFetch.retry(), () => (
            <MaintenancePanel windows={maintenanceWindows} />
          ))}
          {renderRegion(signalsPhase, signalsError, retrySignalsRegion, () => (
            <ComponentsRoster rows={deriveRoster(components, signalsData)} />
          ))}
        </div>
      </div>
    </div>
  )
}
