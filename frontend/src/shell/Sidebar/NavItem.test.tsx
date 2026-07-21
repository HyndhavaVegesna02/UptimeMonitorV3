import { act, fireEvent, render, screen } from '@testing-library/react'
import { SquaresFour } from '@phosphor-icons/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TooltipGroupProvider } from '../useTooltipGroup'
import { NavItem } from './NavItem'

function renderItem(props: Partial<React.ComponentProps<typeof NavItem>> = {}) {
  return render(
    <MemoryRouter>
      <TooltipGroupProvider>
        <NavItem
          path="/dashboard"
          label="Dashboard"
          icon={SquaresFour}
          active={false}
          showTooltip={false}
          {...props}
        />
      </TooltipGroupProvider>
    </MemoryRouter>,
  )
}

describe('NavItem', () => {
  it('renders a real router link with a visible label', () => {
    renderItem()
    const link = screen.getByRole('link', { name: 'Dashboard' })
    expect(link).toHaveAttribute('href', '/dashboard')
  })

  it('marks the active route with aria-current="page"', () => {
    renderItem({ active: true })
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page')
  })

  it('does not set aria-current on an inactive item', () => {
    renderItem({ active: false })
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute('aria-current')
  })

  describe('when collapsed to a rail (showTooltip=true)', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })
    afterEach(() => {
      vi.useRealTimers()
    })

    it('does not show a tooltip immediately on hover — it is delayed', () => {
      renderItem({ showTooltip: true })
      const link = screen.getByRole('link', { name: 'Dashboard' })
      fireEvent.mouseEnter(link)
      expect(screen.queryByRole('tooltip')).toBeNull()
    })

    it('shows the tooltip after the opening delay elapses', () => {
      renderItem({ showTooltip: true })
      const link = screen.getByRole('link', { name: 'Dashboard' })
      fireEvent.mouseEnter(link)
      act(() => {
        vi.advanceTimersByTime(500)
      })
      expect(screen.getByRole('tooltip')).toHaveTextContent('Dashboard')
    })

    it('hides the tooltip on mouse leave', () => {
      renderItem({ showTooltip: true })
      const link = screen.getByRole('link', { name: 'Dashboard' })
      fireEvent.mouseEnter(link)
      act(() => {
        vi.advanceTimersByTime(500)
      })
      fireEvent.mouseLeave(link)
      expect(screen.queryByRole('tooltip')).toBeNull()
    })

    it('never renders a tooltip when showTooltip is false (expanded sidebar)', () => {
      renderItem({ showTooltip: false })
      const link = screen.getByRole('link', { name: 'Dashboard' })
      fireEvent.mouseEnter(link)
      act(() => {
        vi.advanceTimersByTime(500)
      })
      expect(screen.queryByRole('tooltip')).toBeNull()
    })
  })
})
