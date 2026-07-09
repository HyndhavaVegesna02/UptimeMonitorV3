import { render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { server } from '../../mocks/server'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_TOPOLOGY,
} from '../../mocks/handlers'
import { useAvailability } from './useAvailability'
import type { AvailabilityRange } from './windowRange'

/**
 * STORY-068: this file's `<Harness>` drives the heaviest fan-out of any
 * `useFetch`-based hook in the suite — one `getTopology()` hop, THEN (in
 * parallel) `FIXTURE_TOPOLOGY.length` `getComponentAvailability` calls AND
 * `FIXTURE_TOPOLOGY.length` `getHistory` segment calls (STORY-058) — nine
 * MSW round trips per render versus one or two for most other hooks' tests.
 * Under `npm test`'s default file-parallelism, CPU contention across
 * workers can inflate this file's wall-clock past Vitest's 5000ms default
 * even though every individual round trip is a synchronous MSW mock (no
 * artificial delay) — proven contention, not a hook-level leak: this file
 * has an EMPTY diff since the sprint-41 cut, passes reliably in isolation
 * (`--no-file-parallelism`), and forcing every test to time out immediately
 * (`--testTimeout=1`) produces plain timeouts with ZERO unhandled
 * rejections — there is no pending promise this hook leaves uncaught. Per
 * the 2026-07-06 contention-verdict agreement, the sanctioned remedy for a
 * PROVEN-contention gate is an appropriate per-test timeout (NOT a leak
 * papered over) — scoped to just this file via `vi.setConfig`, not a global
 * bump, so unrelated files' 5000ms expectations are untouched.
 */
beforeAll(() => {
  vi.setConfig({ testTimeout: 15000 })
})

afterAll(() => {
  vi.resetConfig()
})

/** Minimal harness rendering every `useAvailability` phase, mirroring how
 * `AvailabilityPage` will drive it. */
function Harness({ range }: { range: AvailabilityRange }) {
  const { state, retry } = useAvailability(range)

  if (state.phase === 'loading') {
    return <div role="status">Loading…</div>
  }

  if (state.phase === 'error') {
    return (
      <div>
        <p role="alert">{state.message}</p>
        <button onClick={retry}>Retry</button>
      </div>
    )
  }

  return (
    <ul>
      {state.data.topology.map((component) => (
        <li key={component.id}>
          {component.name}: {String(state.data.availabilityByComponent[component.id]?.rollup.availability_pct)}
          {' '}segments:{state.data.segmentsByComponent[component.id]?.length ?? 'none'}
        </li>
      ))}
    </ul>
  )
}

const RANGE_A: AvailabilityRange = {
  since: '2026-07-02T00:00:00.000Z',
  until: '2026-07-03T00:00:00.000Z',
}

const RANGE_B: AvailabilityRange = {
  since: '2026-06-26T00:00:00.000Z',
  until: '2026-07-03T00:00:00.000Z',
}

describe('useAvailability', () => {
  it('merges the topology and each component availability into one bundle', async () => {
    render(<Harness range={RANGE_A} />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(FIXTURE_TOPOLOGY.length)

    const firstComponent = FIXTURE_TOPOLOGY[0]
    const firstPct = FIXTURE_AVAILABILITY_BY_COMPONENT[firstComponent.id].rollup.availability_pct
    expect(items[0]).toHaveTextContent(firstComponent.name)
    expect(items[0]).toHaveTextContent(String(firstPct))

    // Zero-signal component's all-None rollup renders honestly (as "null",
    // never a stand-in "0") through this raw harness.
    const zeroSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-orders')
    expect(zeroSignal).toBeDefined()
    const zeroSignalItem = items.find((item) => item.textContent?.includes(zeroSignal!.name))
    expect(zeroSignalItem).toBeDefined()
    expect(zeroSignalItem).toHaveTextContent('null')
  })

  it('reaches the error phase when one component availability call rejects (whole-tab error is acceptable)', async () => {
    const failingId = FIXTURE_TOPOLOGY[1].id
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ params }) => {
        if (params.componentId === failingId) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    render(<Harness range={RANGE_A} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('refetches with the NEW range query params when the range prop changes', async () => {
    const seenSince: string[] = []
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ request, params }) => {
        const url = new URL(request.url)
        seenSince.push(url.searchParams.get('since') ?? '')
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    const { rerender } = render(<Harness range={RANGE_A} />)
    await screen.findAllByRole('listitem')

    expect(seenSince.every((since) => since === RANGE_A.since)).toBe(true)
    seenSince.length = 0

    rerender(<Harness range={RANGE_B} />)

    await waitFor(() => {
      expect(seenSince.length).toBeGreaterThan(0)
    })
    expect(seenSince.every((since) => since === RANGE_B.since)).toBe(true)
  })

  it('builds sparkline segments from the component\'s first signal\'s real history (STORY-058 AC1)', async () => {
    render(<Harness range={RANGE_A} />)

    const items = await screen.findAllByRole('listitem')
    const frontend = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const frontendItem = items.find((item) => item.textContent?.includes(frontend.name))!
    // `sockshop-frontend`'s first signal is `frontend-http`, fixtured with
    // `FIXTURE_HISTORY_FRONTEND_HTTP.length` real observations.
    expect(frontendItem).toHaveTextContent(
      `segments:${FIXTURE_HISTORY_FRONTEND_HTTP.length}`,
    )
  })

  it('never calls getHistory for a zero-signal component — segments stay empty, never fabricated (STORY-058 AC1)', async () => {
    render(<Harness range={RANGE_A} />)

    const items = await screen.findAllByRole('listitem')
    const zeroSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-orders')!
    const zeroSignalItem = items.find((item) => item.textContent?.includes(zeroSignal.name))!
    expect(zeroSignalItem).toHaveTextContent('segments:0')
  })

  it('degrades a single component\'s segment fetch failure to an empty array — never blocks the whole bundle (STORY-058 AC1)', async () => {
    server.use(
      http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    render(<Harness range={RANGE_A} />)

    // The bundle still reaches success — a history failure is an
    // enhancement-only degradation, unlike an availability rollup failure.
    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(FIXTURE_TOPOLOGY.length)
    const frontend = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const frontendItem = items.find((item) => item.textContent?.includes(frontend.name))!
    expect(frontendItem).toHaveTextContent('segments:0')
  })
})
