import { render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { FIXTURE_PROPOSALS } from '../../mocks/handlers'
import { useApprovalsBadge } from './useApprovalsBadge'

/** Minimal harness rendering the badge count (or its absence), the same way
 * `Sidebar`'s `pendingApprovals` prop will be driven by `AppShell`. */
function Harness() {
  const count = useApprovalsBadge()
  return <div data-testid="count">{count === undefined ? 'none' : count}</div>
}

describe('useApprovalsBadge', () => {
  it('resolves to the number of open proposals on success (STORY-056 AC4)', async () => {
    render(<Harness />)

    expect(
      await screen.findByText(String(FIXTURE_PROPOSALS.length)),
    ).toBeInTheDocument()
  })

  it('resolves to zero when there are no open proposals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    render(<Harness />)

    expect(await screen.findByText('0')).toBeInTheDocument()
  })

  it('is undefined while loading (no badge) and on fetch failure (graceful degradation)', async () => {
    let called = false
    server.use(
      http.get('/api/v1/approvals', () => {
        called = true
        return HttpResponse.json({ detail: 'boom' }, { status: 500 })
      }),
    )

    render(<Harness />)

    // Loading, then settles error -> stays "none" (never a stale/fabricated count).
    expect(screen.getByTestId('count')).toHaveTextContent('none')
    await waitFor(() => expect(called).toBe(true))
    expect(screen.getByTestId('count')).toHaveTextContent('none')
  })
})
