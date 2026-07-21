import { http, HttpResponse } from 'msw'
import type { ComponentDTO } from '../../api/types'

/**
 * `GET /api/v1/components` fixture (STORY-121) — a real-shaped sample
 * covering the vendor statuses the shell must map: two operational, one
 * degraded, one under maintenance (the worst-of derivation's non-trivial
 * mix — `overallStatus.test.ts` reuses this same shape).
 */
export const FIXTURE_COMPONENTS: ComponentDTO[] = [
  { id: 'sockshop-frontend', name: 'Frontend Web', status: 'operational' },
  { id: 'sockshop-catalogue', name: 'Catalogue API', status: 'operational' },
  { id: 'sockshop-checkout', name: 'Checkout Flow', status: 'degraded_performance' },
  { id: 'sockshop-payment', name: 'Payment Gateway', status: 'under_maintenance' },
]

/**
 * Default success handler (STORY-121). Tests override with `server.use(...)`
 * for the empty/error paths — MSW is the only mocked I/O edge.
 */
export const componentsHandlers = [
  http.get('/api/v1/components', () => {
    return HttpResponse.json(FIXTURE_COMPONENTS)
  }),
]
