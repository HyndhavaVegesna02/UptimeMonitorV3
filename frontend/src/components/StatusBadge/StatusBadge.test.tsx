import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { defaultStatusLabel, StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it.each([
    ['up', 'Up'],
    ['down', 'Down'],
    ['degraded', 'Degraded'],
    ['partial', 'Partial outage'],
    ['maintenance', 'Maintenance'],
    ['unknown', 'Unknown'],
    ['missing', 'Missing data'],
  ] as const)('renders the %s status with an accessible "%s" label', (status, label) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('renders a decorative status dot alongside the label, not as its only cue', () => {
    const { container } = render(<StatusBadge status="down" />)
    const dot = container.querySelector('.status-badge__dot')
    expect(dot).not.toBeNull()
    expect(dot).toHaveAttribute('aria-hidden', 'true')
    // Status is never color-alone (AC6): the label text must be present too.
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('applies a neutral modifier class for the unknown status', () => {
    const { container } = render(<StatusBadge status="unknown" />)
    expect(container.querySelector('.status-badge--unknown')).not.toBeNull()
  })

  it('accepts a custom label override while keeping the status-based dot color', () => {
    render(<StatusBadge status="up" label="All systems operational" />)
    expect(screen.getByText('All systems operational')).toBeInTheDocument()
  })

  it.each([
    'up',
    'down',
    'degraded',
    'partial',
    'maintenance',
    'unknown',
    'missing',
  ] as const)(
    'applies the status--%s modifier class for its variant styling',
    (status) => {
      const { container } = render(<StatusBadge status={status} />)
      expect(
        container.querySelector(`.status-badge--${status}`),
      ).not.toBeNull()
    },
  )
})

describe('defaultStatusLabel', () => {
  it.each([
    ['up', 'Up'],
    ['down', 'Down'],
    ['degraded', 'Degraded'],
    ['partial', 'Partial outage'],
    ['maintenance', 'Maintenance'],
    ['unknown', 'Unknown'],
    ['missing', 'Missing data'],
  ] as const)(
    'returns the same default label text the %s badge itself renders (single source of truth, STORY-100)',
    (status, label) => {
      expect(defaultStatusLabel(status)).toBe(label)
    },
  )
})
