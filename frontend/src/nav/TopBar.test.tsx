import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { ThemeProvider } from '../theme/ThemeContext'
import { useSampleMode } from '../features/dashboard/useSampleMode'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import { TopBar } from './TopBar'

function mockMatchMedia(prefersDark: boolean, mobileMatches = false) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches:
        query === '(prefers-color-scheme: dark)'
          ? prefersDark
          : query === QUERY_MOBILE_DOWN
            ? mobileMatches
            : false,
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
function TopBarHarness({
  showMenuTrigger,
  onOpenMenu,
  showSampleChip,
  onRestoreBanner,
}: {
  showMenuTrigger?: boolean
  onOpenMenu?: () => void
  showSampleChip?: boolean
  onRestoreBanner?: () => void
}) {
  const sampleMode = useSampleMode()
  return (
    <TopBar
      sampleMode={sampleMode}
      showMenuTrigger={showMenuTrigger}
      onOpenMenu={onOpenMenu}
      showSampleChip={showSampleChip}
      onRestoreBanner={onRestoreBanner}
    />
  )
}

function renderTopBar(
  props: {
    showMenuTrigger?: boolean
    onOpenMenu?: () => void
    showSampleChip?: boolean
    onRestoreBanner?: () => void
  } = {},
  mobileMatches = false,
) {
  mockMatchMedia(true, mobileMatches)
  return render(
    <ThemeProvider>
      <TopBarHarness {...props} />
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

  it('does not render a menu trigger when showMenuTrigger is false (default)', () => {
    renderTopBar()
    expect(
      screen.queryByRole('button', { name: 'Open navigation menu' }),
    ).not.toBeInTheDocument()
  })

  it('renders a labeled menu trigger when showMenuTrigger is true (STORY-096 AC2)', async () => {
    const onOpenMenu = vi.fn()
    renderTopBar({ showMenuTrigger: true, onOpenMenu })

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await userEvent.setup().click(trigger)

    expect(onOpenMenu).toHaveBeenCalledTimes(1)
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

  it('shows a visible "Sample mode" text label next to the switch at desktop widths (AC1)', async () => {
    renderTopBar({}, false)
    await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.getByText('Sample mode')).toBeInTheDocument()
  })

  it('hides the visible text label at mobile widths, keeping the aria-label (AC1)', async () => {
    renderTopBar({}, true)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.queryByText('Sample mode')).not.toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-label', 'Sample mode')
  })

  it('OFF state renders neutral trigger styling — no active/warning class (AC1)', async () => {
    renderTopBar()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).not.toHaveClass('top-bar__trigger--active')
  })

  it('ON state renders the warning-accented trigger class, never the error/red class (AC1)', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderTopBar()
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveClass('top-bar__trigger--active')
    expect(toggle).not.toHaveClass('top-bar__trigger--error')
  })

  it('renders a persistent "SAMPLE" chip when showSampleChip is true, and clicking it calls onRestoreBanner (AC2)', async () => {
    const user = userEvent.setup()
    const onRestoreBanner = vi.fn()
    renderTopBar({ showSampleChip: true, onRestoreBanner })
    await screen.findByRole('switch', { name: 'Sample mode' })

    const chip = screen.getByRole('button', { name: /sample mode is on/i })
    expect(chip).toHaveTextContent('SAMPLE')

    await user.click(chip)
    expect(onRestoreBanner).toHaveBeenCalledTimes(1)
  })

  it('does not render the SAMPLE chip when showSampleChip is false/omitted (AC2)', async () => {
    renderTopBar()
    await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.queryByText('SAMPLE')).not.toBeInTheDocument()
  })

  it("theme toggle's title names the specific action, matching its aria-label", () => {
    renderTopBar()
    const themeButton = screen.getByRole('button', { name: /switch to/i })
    expect(themeButton).toHaveAttribute('title', themeButton.getAttribute('aria-label'))
  })
})
