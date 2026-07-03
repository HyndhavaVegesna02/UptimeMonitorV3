import { render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_AVAILABILITY_BY_COMPONENT, FIXTURE_TOPOLOGY } from '../../mocks/handlers'
import { useAvailability } from './useAvailability'
import type { AvailabilityRange } from './windowRange'

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
})
