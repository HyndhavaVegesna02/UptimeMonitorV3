import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { SampleModeBanner } from './SampleModeBanner'

describe('SampleModeBanner', () => {
  it('renders nothing when not visible', () => {
    render(<SampleModeBanner visible={false} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('renders the warning as a live region when visible (role preserved, AC3)', () => {
    render(<SampleModeBanner visible={true} />)
    expect(
      screen.getByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('is dismissible: clicking Dismiss hides it', async () => {
    const user = userEvent.setup()
    render(<SampleModeBanner visible={true} />)

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))

    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('reappears if it becomes visible again after being dismissed', () => {
    const { rerender } = render(<SampleModeBanner visible={true} />)
    expect(screen.getByRole('status')).toBeInTheDocument()

    rerender(<SampleModeBanner visible={false} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    rerender(<SampleModeBanner visible={true} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('re-arms after a dismiss once visible cycles off then on again (toggle off/on re-surfaces it)', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<SampleModeBanner visible={true} />)

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    rerender(<SampleModeBanner visible={false} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    rerender(<SampleModeBanner visible={true} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('a dismiss while visible does not reappear on an unrelated re-render (still visible=true)', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<SampleModeBanner visible={true} />)

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()

    rerender(<SampleModeBanner visible={true} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
