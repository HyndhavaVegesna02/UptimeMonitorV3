import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { HistoryFilterBar } from './HistoryFilterBar'

function renderBar(overrides: Partial<Parameters<typeof HistoryFilterBar>[0]> = {}) {
  const props = {
    search: '',
    onSearchChange: vi.fn(),
    result: 'all' as const,
    onResultChange: vi.fn(),
    location: 'all',
    onLocationChange: vi.fn(),
    locationOptions: ['SYNTHETIC_LOCATION-0000000000000047', 'SYNTHETIC_LOCATION-0000000000000060'],
    ...overrides,
  }
  render(<HistoryFilterBar {...props} />)
  return props
}

describe('HistoryFilterBar', () => {
  it('renders a labelled search box, Result select, and Location select — every control has an accessible name', () => {
    renderBar()
    expect(screen.getByRole('textbox', { name: /search/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /result/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /location/i })).toBeInTheDocument()
  })

  it('offers the fixed Result vocabulary All/Up/Degraded/Down', () => {
    renderBar()
    const select = screen.getByRole('combobox', { name: /result/i }) as HTMLSelectElement
    const optionLabels = Array.from(select.options).map((option) => option.textContent)
    expect(optionLabels).toEqual(['All', 'Up', 'Degraded', 'Down'])
  })

  it('offers an "All locations" option plus one per derived location', () => {
    renderBar()
    const select = screen.getByRole('combobox', { name: /location/i }) as HTMLSelectElement
    expect(select.options).toHaveLength(3)
    expect(select.options[0].textContent).toMatch(/all/i)
  })

  it('calls onSearchChange as the operator types', async () => {
    const user = userEvent.setup()
    const props = renderBar()
    await user.type(screen.getByRole('textbox', { name: /search/i }), 'a')
    expect(props.onSearchChange).toHaveBeenCalled()
  })

  it('calls onResultChange when a new Result option is picked', async () => {
    const user = userEvent.setup()
    const props = renderBar()
    await user.selectOptions(screen.getByRole('combobox', { name: /result/i }), 'down')
    expect(props.onResultChange).toHaveBeenCalledWith('down')
  })

  it('calls onLocationChange when a new Location option is picked', async () => {
    const user = userEvent.setup()
    const props = renderBar()
    await user.selectOptions(
      screen.getByRole('combobox', { name: /location/i }),
      'SYNTHETIC_LOCATION-0000000000000047',
    )
    expect(props.onLocationChange).toHaveBeenCalledWith('SYNTHETIC_LOCATION-0000000000000047')
  })
})
