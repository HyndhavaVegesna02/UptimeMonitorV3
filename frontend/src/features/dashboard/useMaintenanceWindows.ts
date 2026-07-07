import { getMaintenance } from '../../api/client'
import type { MaintenanceWindowDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type MaintenanceWindowsFetchState = FetchState<MaintenanceWindowDTO[]>

export type UseMaintenanceWindowsResult = UseFetchResult<MaintenanceWindowDTO[]>

/**
 * Fetch hook for `GET /api/v1/maintenance`, consumed by the Dashboard tab
 * (STORY-046) to overlay a maintenance indicator ALONGSIDE component health.
 * Health and maintenance are SEPARATE concepts (dossier §6/§11): health
 * comes from `GET /api/v1/components` via `useComponents`/`toHealthStatus`,
 * while "is this component under maintenance right now" is derived
 * CLIENT-SIDE from these windows via
 * `features/maintenance/windowState.ts::deriveWindowState` — this hook never
 * touches `ComponentStatus`/`statusMapping.ts`. A thin `useFetch` wrapper,
 * mirroring `useComponents.ts`'s pattern exactly.
 *
 * The overlay is an ENHANCEMENT, not a hard dependency: the Dashboard treats
 * any non-`'success'` state from this hook (loading OR error) as "no active
 * windows" rather than blocking or erroring the primary components table —
 * see `DashboardPage.tsx`'s graceful-degradation comment.
 */
export function useMaintenanceWindows(): UseMaintenanceWindowsResult {
  return useFetch(getMaintenance)
}
