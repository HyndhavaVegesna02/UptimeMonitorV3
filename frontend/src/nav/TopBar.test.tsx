import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { ThemeProvider } from '../theme/ThemeContext'
import { useSampleMode } from '../features/dashboard/useSampleMode'
import { TopBar } from './TopBar'

function mockMatchMedia(prefersDark: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-color-scheme: dark)' && prefersDark,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

/** Drives `TopBar` off the REAL `useSampleMode` hook, mirroring how
 * `AppShell` lifts the hook once and passes its result down to both
 * `TopBar` and `SampleModeBanner` (a single source of truth — see that
 * file's header comment for why two independent hook instances would
 * desync). */
function TopBarHarness() {
  const sampleMode = useSampleMode()
  return <TopBar sampleMode={sampleMode} />
}

function renderTopBar() {
  mockMatchMedia(true)
  return render(
    <ThemeProvider>
      <TopBarHarness />
    </ThemeProvider>,
  )
}

describe('TopBar', () => {
  it('renders a theme toggle control (kept from the old Nav)', () => {
    renderTopBar()
    expect(
      screen.getByRole('button', { name: /switch to/i }),
    ).toBeInTheDocument()
  })

  it('does not render the sample-mode trigger until the initial GET resolves (loading case)', () => {
    renderTopBar()
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })

  it('renders the sample-mode trigger reflecting the GET-loaded state (off), role+state preserved (AC2)', async () => {
    renderTopBar()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('renders the trigger already-on when the flag is already on', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderTopBar()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('PUTs the requested value on click and reflects the response (no optimistic flip, AC2)', async () => {
    const user = userEvent.setup()
    let receivedBody: unknown
    server.use(
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: true })
      }),
    )

    renderTopBar()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'))
    expect(receivedBody).toEqual({ enabled: true })
  })

  it('disables the trigger while a PUT is in flight', async () => {
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

    renderTopBar()
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

    renderTopBar()
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

    renderTopBar()

    const retryButton = await screen.findByRole('button', {
      name: /sample mode unavailable/i,
    })
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()

    await user.click(retryButton)

    expect(await screen.findByRole('switch', { name: 'Sample mode' })).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
