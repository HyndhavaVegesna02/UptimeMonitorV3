import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ThemeProvider } from '../theme/ThemeContext'
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

function renderTopBar() {
  mockMatchMedia(true)
  return render(
    <ThemeProvider>
      <TopBar />
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
})
