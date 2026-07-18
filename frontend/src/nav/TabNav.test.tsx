import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { TABS } from './tabs'
import { TabNav } from './TabNav'

function renderTabNav(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <TabNav />
    </MemoryRouter>,
  )
}

describe('TabNav', () => {
  it('renders one link per tab, each carrying an icon + visible text label', () => {
    renderTabNav()
    for (const tab of TABS) {
      const link = screen.getByRole('link', { name: tab.label })
      expect(link).toBeInTheDocument()
      expect(link.querySelector('svg')).not.toBeNull()
      expect(screen.getByText(tab.label)).toBeInTheDocument()
    }
  })

  it('marks the active route with aria-current="page" (AC1)', () => {
    renderTabNav('/availability')
    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute('aria-current')
  })

  it('marks only the root route active at "/", not every other tab', () => {
    renderTabNav('/')
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    for (const tab of TABS.slice(1)) {
      expect(screen.getByRole('link', { name: tab.label })).not.toHaveAttribute('aria-current')
    }
  })

  it('renders the active tab with a visible teal indicator class, not color alone', () => {
    renderTabNav('/approvals')
    expect(screen.getByRole('link', { name: 'Approvals' })).toHaveClass('tab-nav__tab--active')
  })

  it('is labeled as the Primary navigation landmark', () => {
    renderTabNav()
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
  })

  it('calls onNavigate when a tab link is activated (sheet-close contract)', async () => {
    const { default: userEvent } = await import('@testing-library/user-event')
    const user = userEvent.setup()
    const calls: number[] = []
    render(
      <MemoryRouter initialEntries={['/']}>
        <TabNav onNavigate={() => calls.push(1)} />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('link', { name: 'Availability' }))
    expect(calls).toHaveLength(1)
  })
})
