import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FIXTURE_COMPONENTS } from '../../mocks/handlers/components'
import { server } from '../../mocks/server'
import { ScheduleMaintenanceForm } from './ScheduleMaintenanceForm'

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.selectOptions(screen.getByLabelText(/component/i), 'sockshop-checkout')
  await user.type(screen.getByLabelText(/^start/i), '2026-07-22T10:00')
  await user.type(screen.getByLabelText(/^end/i), '2026-07-22T12:00')
}

describe('ScheduleMaintenanceForm', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('AC6: shows a loading state while components are in flight', () => {
    server.use(http.get('/api/v1/components', async () => new Promise(() => {})))
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('AC6: shows an error state with retry when components fail to load', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('AC2/AC6: every field has an associated label, and the component select lists the loaded components', async () => {
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)

    expect(await screen.findByLabelText(/component/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^start/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^end/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/reason/i)).toBeInTheDocument()

    for (const component of FIXTURE_COMPONENTS) {
      expect(screen.getByRole('option', { name: component.name })).toBeInTheDocument()
    }
  })

  it('AC1: Start/End are wrapped in the styled datetime control (still real datetime-local inputs, unchanged type/value semantics)', async () => {
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)
    await screen.findByLabelText(/component/i)

    const startInput = screen.getByLabelText(/^start/i)
    const endInput = screen.getByLabelText(/^end/i)

    // Still the same underlying control (STORY-132's UTC conversion +
    // datetime-local value semantics are byte-identical) — only the visual
    // wrapper is new. This is a NECESSARY-not-SUFFICIENT check: it proves
    // the styled wrapper markup exists, not that it renders legibly — the
    // live reality gate is what confirms the actual visual result.
    expect(startInput).toHaveAttribute('type', 'datetime-local')
    expect(endInput).toHaveAttribute('type', 'datetime-local')
    expect(startInput.closest('.schedule-maintenance-form__datetime')).not.toBeNull()
    expect(endInput.closest('.schedule-maintenance-form__datetime')).not.toBeNull()
  })

  it('AC3: blocks submit client-side when end <= start, without calling the API, and marks ends_at invalid', async () => {
    let called = false
    server.use(
      http.post('/api/v1/maintenance', () => {
        called = true
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)
    await screen.findByLabelText(/component/i)

    await user.selectOptions(screen.getByLabelText(/component/i), 'sockshop-checkout')
    await user.type(screen.getByLabelText(/^start/i), '2026-07-22T12:00')
    await user.type(screen.getByLabelText(/^end/i), '2026-07-22T10:00')
    await user.click(screen.getByRole('button', { name: /schedule/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByLabelText(/^end/i)).toHaveAttribute('aria-invalid', 'true')
    expect(called).toBe(false)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC2: converts datetime-local to UTC ISO, POSTs, resets the form, and calls onScheduled on 201 success', async () => {
    const onScheduled = vi.fn()
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/maintenance', async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json(
          {
            id: 4,
            component_id: 'sockshop-checkout',
            starts_at: '2026-07-22T10:00:00Z',
            ends_at: '2026-07-22T12:00:00Z',
            reason: null,
            title: null,
          },
          { status: 201 },
        )
      }),
    )
    const user = userEvent.setup()
    render(<ScheduleMaintenanceForm onScheduled={onScheduled} />)
    await screen.findByLabelText(/component/i)
    await fillValidForm(user)

    await user.click(screen.getByRole('button', { name: /schedule/i }))

    await waitFor(() => expect(onScheduled).toHaveBeenCalledTimes(1))
    expect(capturedBody).toMatchObject({ component_id: 'sockshop-checkout' })
    expect((capturedBody as { starts_at: string }).starts_at.endsWith('Z')).toBe(true)
    expect((screen.getByLabelText(/^start/i) as HTMLInputElement).value).toBe('')
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('CRUX AC3: a forced end-before-start 422 from the server maps to the ends_at field inline (not starts_at)', async () => {
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'ends_at must be strictly greater than starts_at.' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)
    await screen.findByLabelText(/component/i)
    await fillValidForm(user)

    await user.click(screen.getByRole('button', { name: /schedule/i }))

    const endInput = await screen.findByLabelText(/^end/i)
    expect(endInput).toHaveAttribute('aria-invalid', 'true')
    const describedBy = endInput.getAttribute('aria-describedby')
    expect(describedBy).toBeTruthy()
    const errorNode = document.getElementById(describedBy!)
    expect(errorNode).toHaveAttribute('role', 'alert')
    expect(errorNode).toHaveTextContent('ends_at must be strictly greater than starts_at.')
    // Crucially NOT mapped to starts_at, even though the message names it too.
    expect(screen.getByLabelText(/^start/i)).toHaveAttribute('aria-invalid', 'false')
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('a 422 detail naming none of the fields renders a form-level banner', async () => {
    server.use(
      http.post('/api/v1/maintenance', () => HttpResponse.json({ detail: 'Internal server error' }, { status: 422 })),
    )
    const user = userEvent.setup()
    render(<ScheduleMaintenanceForm onScheduled={vi.fn()} />)
    await screen.findByLabelText(/component/i)
    await fillValidForm(user)

    await user.click(screen.getByRole('button', { name: /schedule/i }))

    expect(await screen.findByText('Internal server error')).toBeInTheDocument()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
