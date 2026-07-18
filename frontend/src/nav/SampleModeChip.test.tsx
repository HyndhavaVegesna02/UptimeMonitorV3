import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { SampleModeChip } from './SampleModeChip'

describe('SampleModeChip (STORY-104 AC3, ported contract)', () => {
  it('renders the SAMPLE text', () => {
    render(<SampleModeChip onRestore={vi.fn()} />)
    expect(screen.getByRole('button', { name: /sample mode is on/i })).toHaveTextContent(
      'SAMPLE',
    )
  })

  it('calls onRestore when clicked', async () => {
    const user = userEvent.setup()
    const onRestore = vi.fn()
    render(<SampleModeChip onRestore={onRestore} />)

    await user.click(screen.getByRole('button', { name: /sample mode is on/i }))

    expect(onRestore).toHaveBeenCalledTimes(1)
  })
})
