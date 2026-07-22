import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { PublicationDTO } from '../../api/types'
import { PublicationsTimeline } from './PublicationsTimeline'

const SUCCEEDED_ENTRY: PublicationDTO = {
  id: 1,
  component_id: 'http-check',
  status: 'operational',
  published_at: '2026-07-21T08:05:00Z',
  proposal_id: 1,
  outcome: 'succeeded',
  author: 'dashboard-operator',
}

const FAILED_NULL_EDGES_ENTRY: PublicationDTO = {
  id: 2,
  component_id: 'http-check',
  status: 'operational',
  published_at: '2026-07-21T07:05:00Z',
  proposal_id: null,
  outcome: 'failed',
  author: null,
}

describe('PublicationsTimeline', () => {
  it('AC1: renders each entry with component, health badge, outcome chip, time, proposal id, and author', () => {
    render(<PublicationsTimeline publications={[SUCCEEDED_ENTRY]} />)

    const row = screen.getByRole('row', { name: /http-check/i })
    expect(within(row).getByText('http-check')).toBeInTheDocument()
    expect(within(row).getByText('Up')).toBeInTheDocument()
    expect(within(row).getByText('Succeeded')).toBeInTheDocument()
    expect(within(row).getByText('1')).toBeInTheDocument()
    expect(within(row).getByText('dashboard-operator')).toBeInTheDocument()
  })

  it('AC1 CRUX: outcome is a distinct chip from the health status, not conflated even when status is ok-ish', () => {
    render(<PublicationsTimeline publications={[FAILED_NULL_EDGES_ENTRY]} />)

    // A "failed" outcome alongside an "operational" (Up) status must render
    // BOTH distinctly — never collapse the failed outcome into the health
    // badge or vice versa.
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('right-aligns the numeric Proposal column (header + cells), review refinement sprint-60', () => {
    render(<PublicationsTimeline publications={[SUCCEEDED_ENTRY]} />)

    expect(screen.getByRole('columnheader', { name: 'Proposal' })).toHaveClass('is-numeric')
    ;['Time', 'Component', 'Status', 'Outcome', 'Author'].forEach((name) => {
      expect(screen.getByRole('columnheader', { name })).not.toHaveClass('is-numeric')
    })

    const row = screen.getByRole('row', { name: /http-check/i })
    const proposalCell = within(row).getByText('1')
    expect(proposalCell).toHaveClass('is-numeric')
  })

  it('proposal_id: null renders "—", never "0"', () => {
    render(<PublicationsTimeline publications={[FAILED_NULL_EDGES_ENTRY]} />)

    expect(screen.getByText('—', { selector: '.publications-timeline__proposal' })).toBeInTheDocument()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('author: null renders "—"', () => {
    render(<PublicationsTimeline publications={[FAILED_NULL_EDGES_ENTRY]} />)

    expect(screen.getByText('—', { selector: '.publications-timeline__author' })).toBeInTheDocument()
  })

  it('AC2: renders no fabricated fields — no incident_id text anywhere', () => {
    render(<PublicationsTimeline publications={[SUCCEEDED_ENTRY, FAILED_NULL_EDGES_ENTRY]} />)

    expect(screen.queryByText(/incident/i)).not.toBeInTheDocument()
  })

  it('renders rows in the exact given order, without re-sorting (most-recent-first as returned)', () => {
    const olderFirst: PublicationDTO[] = [FAILED_NULL_EDGES_ENTRY, SUCCEEDED_ENTRY]
    render(<PublicationsTimeline publications={olderFirst} />)

    const rows = screen.getAllByRole('row').filter((row) => row.querySelector('td'))
    expect(rows).toHaveLength(2)
    // FAILED_NULL_EDGES_ENTRY (published 07:05) is listed first in the given
    // array even though it is chronologically earlier than SUCCEEDED_ENTRY
    // (08:05) — the component must not re-sort it back to newest-first.
    expect(within(rows[0]).getByText('Failed')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Succeeded')).toBeInTheDocument()
  })
})
