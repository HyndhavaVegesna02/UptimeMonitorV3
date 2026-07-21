import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { deriveMaintenanceStatus } from '../../features/maintenance/deriveMaintenanceStatus'
import { AppRoutes } from '../../routes'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/maintenance']}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

const TEST_MAINTENANCE_WINDOW = {
  id: 1,
  component_id: 'http-check',
  starts_at: '2026-07-22T02:00:00Z',
  ends_at: '2026-07-22T04:00:00Z',
  title: 'Planned DB upgrade',
  reason: 'Upgrading DynamoDB local cluster',
}

describe('MaintenancePage (STORY-132)', () => {
  it('derives maintenance status correctly', () => {
    const now = new Date('2026-07-22T12:00:00Z')
    expect(
      deriveMaintenanceStatus('2026-07-22T14:00:00Z', '2026-07-22T16:00:00Z', now),
    ).toBe('upcoming')
    expect(
      deriveMaintenanceStatus('2026-07-22T10:00:00Z', '2026-07-22T14:00:00Z', now),
    ).toBe('active')
    expect(
      deriveMaintenanceStatus('2026-07-22T08:00:00Z', '2026-07-22T10:00:00Z', now),
    ).toBe('past')
  })

  it('renders scheduled windows list and schedule form', async () => {
    server.use(
      http.get('/api/v1/maintenance', () => {
        return HttpResponse.json([TEST_MAINTENANCE_WINDOW])
      }),
    )

    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Maintenance' })).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Planned DB upgrade')).toBeInTheDocument()
    })
  })

  it('maps 422 end-before-start validation error strictly to ends_at field (mandatory test)', async () => {
    server.use(
      http.get('/api/v1/maintenance', () => {
        return HttpResponse.json([TEST_MAINTENANCE_WINDOW])
      }),
      http.post('/api/v1/maintenance', () => {
        return HttpResponse.json(
          {
            detail: [
              {
                loc: ['body', 'ends_at'],
                msg: 'value_error: ends_at must be strictly greater than starts_at',
                type: 'value_error',
              },
            ],
          },
          { status: 422 },
        )
      }),
    )

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Planned DB upgrade')).toBeInTheDocument()
    })

    const startsAtInput = screen.getByLabelText('Starts At')
    const endsAtInput = screen.getByLabelText('Ends At')

    await user.type(startsAtInput, '2026-07-22T14:00')
    await user.type(endsAtInput, '2026-07-22T15:00')

    const submitBtn = screen.getByRole('button', { name: 'Schedule Window' })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(
        screen.getByText(/ends_at must be strictly greater than starts_at/i),
      ).toBeInTheDocument()
    })
  })
})
