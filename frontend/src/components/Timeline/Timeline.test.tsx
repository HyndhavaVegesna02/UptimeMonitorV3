import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Timeline, TimelineItem } from './Timeline'

describe('Timeline', () => {
  it('renders as a list with one listitem per entry', () => {
    render(
      <Timeline aria-label="Publication log">
        <TimelineItem>First entry</TimelineItem>
        <TimelineItem isLast>Second entry</TimelineItem>
      </Timeline>,
    )
    expect(screen.getByRole('list', { name: 'Publication log' })).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('First entry')).toBeInTheDocument()
    expect(screen.getByText('Second entry')).toBeInTheDocument()
  })

  it('renders a decorative dot per item, not the sole carrier of content', () => {
    const { container } = render(
      <Timeline>
        <TimelineItem tone="down">Outage published</TimelineItem>
      </Timeline>,
    )
    const dot = container.querySelector('.timeline__dot')
    expect(dot).not.toBeNull()
    expect(dot).toHaveAttribute('aria-hidden', 'true')
    expect(screen.getByText('Outage published')).toBeInTheDocument()
  })

  it('applies the tone modifier class for the dot color', () => {
    const { container } = render(
      <Timeline>
        <TimelineItem tone="up">Recovered</TimelineItem>
      </Timeline>,
    )
    expect(container.querySelector('.timeline__dot--up')).not.toBeNull()
  })

  it('omits the connector line below the last item', () => {
    const { container } = render(
      <Timeline>
        <TimelineItem>Middle</TimelineItem>
        <TimelineItem isLast>Last</TimelineItem>
      </Timeline>,
    )
    const items = container.querySelectorAll('.timeline__item')
    expect(items[0].querySelector('.timeline__line')).not.toBeNull()
    expect(items[1].querySelector('.timeline__line')).toBeNull()
  })
})
