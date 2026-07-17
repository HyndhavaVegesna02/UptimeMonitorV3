import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Toast } from './Toast'

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the message as a polite live region (never role="alert")', () => {
    render(<Toast message="Window scheduled" onDismiss={vi.fn()} />)
    const toast = screen.getByRole('status')
    expect(toast).toHaveTextContent('Window scheduled')
    expect(toast).toHaveAttribute('aria-live', 'polite')
  })

  it('does not steal focus on mount', () => {
    render(<Toast message="Window scheduled" onDismiss={vi.fn()} />)
    expect(screen.getByRole('status')).not.toHaveFocus()
    expect(document.activeElement).toBe(document.body)
  })

  it('auto-dismisses after the default ~4s duration', () => {
    const onDismiss = vi.fn()
    render(<Toast message="Window scheduled" onDismiss={onDismiss} />)

    expect(onDismiss).not.toHaveBeenCalled()
    vi.advanceTimersByTime(3999)
    expect(onDismiss).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('honors a custom duration', () => {
    const onDismiss = vi.fn()
    render(<Toast message="Window deleted" duration={1000} onDismiss={onDismiss} />)

    vi.advanceTimersByTime(999)
    expect(onDismiss).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('restarts the countdown when the message changes (a fresh toast is not cut short)', () => {
    const onDismiss = vi.fn()
    const { rerender } = render(
      <Toast message="Window scheduled" duration={1000} onDismiss={onDismiss} />,
    )

    vi.advanceTimersByTime(700)
    rerender(<Toast message="Window deleted" duration={1000} onDismiss={onDismiss} />)
    vi.advanceTimersByTime(700)
    expect(onDismiss).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('clears its timer on unmount (no dismiss call after unmount)', () => {
    const onDismiss = vi.fn()
    const { unmount } = render(
      <Toast message="Window scheduled" duration={1000} onDismiss={onDismiss} />,
    )
    unmount()
    vi.advanceTimersByTime(2000)
    expect(onDismiss).not.toHaveBeenCalled()
  })
})
