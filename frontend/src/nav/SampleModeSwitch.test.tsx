import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { useSampleMode } from '../features/dashboard/useSampleMode'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import { SampleModeSwitch } from './SampleModeSwitch'

function mockMatchMedia(mobileMatches = false) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === QUERY_MOBILE_DOWN ? mobileMatches : false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

/** Drives `SampleModeSwitch` off the REAL `useSampleMode` hook, mirroring
 * how `AppShell` lifts the hook once and passes its result down (see
 * `AppShell.tsx`'s header comment for why two independent hook instances
 * would desync). */
function Harness() {
  const sampleMode = useSampleMode()
  return <SampleModeSwitch sampleMode={sampleMode} />
}

function renderSwitch(mobileMatches = false) {
  mockMatchMedia(mobileMatches)
  return render(<Harness />)
}

describe('SampleModeSwitch (STORY-104 AC3, ported contract)', () => {
  it('does not render the switch until the initial GET resolves (loading case)', () => {
    renderSwitch()
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })

  it('renders the switch reflecting the GET-loaded state (off), role+state preserved', async () => {
    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('renders already-on when the flag is already on', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('PUTs the requested value on click and reflects the response (no optimistic flip)', async () => {
    const user = userEvent.setup()
    let receivedBody: unknown
    server.use(
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: true })
      }),
    )

    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'))
    expect(receivedBody).toEqual({ enabled: true })
  })

  it('disables the switch while a PUT is in flight', async () => {
    const user = userEvent.setup()
    let resolvePut: (() => void) | undefined
    server.use(
      http.put('/api/v1/sample-mode', async () => {
        await new Promise<void>((resolve) => {
          resolvePut = resolve
        })
        return HttpResponse.json({ enabled: true })
      }),
    )

    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })

    await user.click(toggle)
    await waitFor(() => expect(toggle).toBeDisabled())

    resolvePut?.()
    await waitFor(() => expect(toggle).not.toBeDisabled())
  })

  it('on a failed PUT, surfaces a visible alert and leaves aria-checked unchanged', async () => {
    const user = userEvent.setup()
    server.use(
      http.put('/api/v1/sample-mode', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })

    await user.click(toggle)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('on a GET failure, renders a retry affordance instead of the switch', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/sample-mode', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json({ enabled: false })
      }),
    )

    renderSwitch()

    const retryButton = await screen.findByRole('button', {
      name: /sample mode unavailable/i,
    })
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()

    await user.click(retryButton)

    expect(await screen.findByRole('switch', { name: 'Sample mode' })).toBeInTheDocument()
    expect(callCount).toBe(2)
  })

  it('shows a visible "Sample mode" text label next to the switch at desktop widths (>=768px)', async () => {
    renderSwitch(false)
    await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.getByText('Sample mode')).toBeInTheDocument()
  })

  it('hides the visible text label at mobile widths, keeping the aria-label', async () => {
    renderSwitch(true)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.queryByText('Sample mode')).not.toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-label', 'Sample mode')
  })

  it('OFF state renders neutral styling — no active/warning class', async () => {
    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).not.toHaveClass('sample-mode-switch__toggle--active')
  })

  it('ON state renders the warning-accented class, never the error/red class', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderSwitch()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveClass('sample-mode-switch__toggle--active')
    expect(toggle).not.toHaveClass('sample-mode-switch__retry')
  })
})
