import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TABS } from './tabs'
import { CommandBar, type CommandBarProps } from './CommandBar'
import { ThemeProvider } from '../theme/ThemeContext'
import type { UseSampleModeResult } from '../features/dashboard/useSampleMode'

function mockMatchMedia(mobileMatches = false) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === '(max-width: 768px)' && mobileMatches,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

function makeSampleModeStub(
  overrides: Partial<UseSampleModeResult> = {},
): UseSampleModeResult {
  return {
    state: { phase: 'success', data: { enabled: false } },
    retry: vi.fn(),
    enabled: false,
    setEnabled: vi.fn(),
    mutating: false,
    mutationError: null,
    ...overrides,
  }
}

function renderCommandBar(initialPath = '/', props: Partial<CommandBarProps> = {}) {
  mockMatchMedia()
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <CommandBar
          overallStatus={undefined}
          fetchedAtIso={undefined}
          sampleMode={makeSampleModeStub()}
          showSampleChip={false}
          onRestoreBanner={vi.fn()}
          {...props}
        />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  window.localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('CommandBar — scaffold (STORY-104 Step 1)', () => {
  it('renders the brand', () => {
    renderCommandBar()
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
  })

  it('renders all six tabs (icon + label) via the shared TabNav', () => {
    renderCommandBar()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('reflects the active route via aria-current', () => {
    renderCommandBar('/publications')
    expect(screen.getByRole('link', { name: 'Publications' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('renders a right-cluster region for mode controls', () => {
    const { container } = renderCommandBar()
    expect(container.querySelector('.command-bar__cluster')).not.toBeNull()
  })

  it('is a persistent <header>, not hidden behind any route', () => {
    renderCommandBar()
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})

describe('CommandBar — overall-status dot (STORY-104 Step 2, AC2)', () => {
  it('renders the worst-of overall-status dot beside the brand', () => {
    const { container } = renderCommandBar('/', { overallStatus: 'down' })
    const brand = container.querySelector('.command-bar__brand')
    expect(brand?.querySelector('.status-dot')).not.toBeNull()
    expect(screen.getByText('Overall status: Down')).toBeInTheDocument()
  })

  it('renders "Unknown" while the status has not loaded yet', () => {
    renderCommandBar('/', { overallStatus: undefined })
    expect(screen.getByText('Overall status: Unknown')).toBeInTheDocument()
  })
})

describe('CommandBar — right cluster (STORY-104 Step 3, AC3)', () => {
  it('renders the sample-mode switch reflecting the passed-in state', () => {
    renderCommandBar('/', { sampleMode: makeSampleModeStub({ enabled: true }) })
    expect(screen.getByRole('switch', { name: 'Sample mode' })).toHaveAttribute(
      'aria-checked',
      'true',
    )
  })

  it('renders the persistent SAMPLE chip only when showSampleChip is true', () => {
    renderCommandBar('/', { showSampleChip: false })
    expect(screen.queryByText('SAMPLE')).not.toBeInTheDocument()
  })

  it('renders the SAMPLE chip and wires it to onRestoreBanner', async () => {
    const user = userEvent.setup()
    const onRestoreBanner = vi.fn()
    renderCommandBar('/', { showSampleChip: true, onRestoreBanner })

    const chip = screen.getByRole('button', { name: /sample mode is on/i })
    expect(chip).toHaveTextContent('SAMPLE')

    await user.click(chip)
    expect(onRestoreBanner).toHaveBeenCalledTimes(1)
  })

  it('renders a theme toggle reflecting the current theme', () => {
    renderCommandBar()
    expect(screen.getByRole('button', { name: /switch to/i })).toBeInTheDocument()
  })

  it('toggles the theme when the toggle is clicked', async () => {
    const user = userEvent.setup()
    renderCommandBar()

    const toggle = screen.getByRole('button', { name: 'Switch to light theme' })
    await user.click(toggle)

    expect(screen.getByRole('button', { name: 'Switch to dark theme' })).toBeInTheDocument()
  })

  it('renders "Updated <relative time>" once a fetch timestamp is available', () => {
    renderCommandBar('/', { fetchedAtIso: new Date().toISOString() })
    expect(screen.getByText(/updated/i)).toBeInTheDocument()
    expect(screen.getByText('just now')).toBeInTheDocument()
  })

  it('renders no "Updated" text before the first fetch resolves', () => {
    renderCommandBar('/', { fetchedAtIso: undefined })
    expect(screen.queryByText(/updated/i)).not.toBeInTheDocument()
  })
})
