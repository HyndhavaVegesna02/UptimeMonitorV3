import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { TABS } from './tabs'
import { CommandBar } from './CommandBar'

function renderCommandBar(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <CommandBar />
    </MemoryRouter>,
  )
}

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
