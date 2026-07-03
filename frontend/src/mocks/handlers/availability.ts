import { http, HttpResponse } from 'msw'
import type {
  AvailabilityDTO,
  ComponentAvailabilityDTO,
  ComponentTopologyDTO,
  SignalAvailabilityDTO,
} from '../../api/types'

// NOTE: `availability_pct`/`completeness_pct` are 0-1 FRACTIONS on the wire
// (STORY-015d fix; backend never pre-multiplies by 100) — these fixtures
// mirror the real scale so tests exercise the actual contract.
function makeAvailability(overrides: Partial<AvailabilityDTO> = {}): AvailabilityDTO {
  return {
    availability_pct: 0.9987,
    completeness_pct: 1,
    total_verdicts: 96,
    passing_verdicts: 95,
    maintenance_verdicts: 1,
    gap_verdicts: 0,
    distinct_locations: 3,
    window: '24h',
    computed_at: '2026-07-03T00:00:00Z',
    ...overrides,
  }
}

function makeSignalAvailability(
  signalKey: string,
  overrides: Partial<AvailabilityDTO> = {},
): SignalAvailabilityDTO {
  return { ...makeAvailability(overrides), signal_key: signalKey }
}

/** The all-None degenerate rollup (dossier §11 `rollup_group([])`/no-data
 * window) — zero counts, both percentages null, never a 500. */
function degenerateAvailability(): AvailabilityDTO {
  return makeAvailability({
    availability_pct: null,
    completeness_pct: null,
    total_verdicts: 0,
    passing_verdicts: 0,
    maintenance_verdicts: 0,
    gap_verdicts: 0,
    distinct_locations: 0,
  })
}

/**
 * Topology fixture covering STORY-015d's shapes (AC1, AC3): a multi-signal
 * component, a single-signal component, a zero-signal component, and a
 * component whose window has no data yet (null-pct case).
 */
export const FIXTURE_TOPOLOGY: ComponentTopologyDTO[] = [
  {
    id: 'sockshop-frontend',
    name: 'Sock Shop — frontend',
    signals: [
      {
        signal_key: 'frontend-http',
        name: 'Frontend HTTP check',
        interval_seconds: 60,
        component_id: 'sockshop-frontend',
      },
      {
        signal_key: 'frontend-tls',
        name: 'Frontend TLS check',
        interval_seconds: 300,
        component_id: 'sockshop-frontend',
      },
    ],
  },
  {
    id: 'sockshop-catalogue',
    name: 'Sock Shop — catalogue',
    signals: [
      {
        signal_key: 'catalogue-http',
        name: 'Catalogue HTTP check',
        interval_seconds: 60,
        component_id: 'sockshop-catalogue',
      },
    ],
  },
  {
    id: 'sockshop-orders',
    name: 'Sock Shop — orders',
    signals: [],
  },
  {
    id: 'sockshop-nodata',
    name: 'Sock Shop — nodata',
    signals: [
      {
        signal_key: 'nodata-http',
        name: 'Nodata HTTP check',
        interval_seconds: 60,
        component_id: 'sockshop-nodata',
      },
    ],
  },
]

/**
 * Per-component `ComponentAvailabilityDTO` fixtures keyed by `component_id`
 * (STORY-015d AC1, AC3). `sockshop-orders` is the zero-signal, all-None
 * rollup case; `sockshop-nodata` is the no-data-window case (null
 * availability/completeness at BOTH the rollup and its one signal).
 */
export const FIXTURE_AVAILABILITY_BY_COMPONENT: Record<string, ComponentAvailabilityDTO> = {
  'sockshop-frontend': {
    component_id: 'sockshop-frontend',
    rollup: makeAvailability({ availability_pct: 0.995, completeness_pct: 0.999 }),
    signals: [
      makeSignalAvailability('frontend-http', {
        availability_pct: 0.999,
        completeness_pct: 1,
      }),
      makeSignalAvailability('frontend-tls', {
        availability_pct: 0.995,
        completeness_pct: 0.999,
      }),
    ],
  },
  'sockshop-catalogue': {
    component_id: 'sockshop-catalogue',
    rollup: makeAvailability({ availability_pct: 0.982, completeness_pct: 0.975 }),
    signals: [
      makeSignalAvailability('catalogue-http', {
        availability_pct: 0.982,
        completeness_pct: 0.975,
      }),
    ],
  },
  'sockshop-orders': {
    component_id: 'sockshop-orders',
    rollup: degenerateAvailability(),
    signals: [],
  },
  'sockshop-nodata': {
    component_id: 'sockshop-nodata',
    rollup: degenerateAvailability(),
    signals: [
      { ...degenerateAvailability(), signal_key: 'nodata-http' },
    ],
  },
}

/**
 * Availability/topology feature's default success handlers (STORY-015d
 * AC1). Tests override with `server.use(...)` for empty-topology/error
 * paths — MSW is the only mocked I/O edge; nothing mocks the api client or
 * the hook/page itself.
 */
export const availabilityHandlers = [
  http.get('/api/v1/topology', () => HttpResponse.json(FIXTURE_TOPOLOGY)),
  http.get('/api/v1/availability/component/:componentId', ({ params }) => {
    const componentId = params.componentId as string
    const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[componentId]
    if (!dto) {
      return HttpResponse.json({ detail: 'not found' }, { status: 404 })
    }
    return HttpResponse.json(dto)
  }),
]
