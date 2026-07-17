import { useEffect } from 'react'
import './Toast.css'

export interface ToastProps {
  message: string
  /** Milliseconds before auto-dismiss (STORY-102 AC4: "auto-dismiss ~4s"). */
  duration?: number
  onDismiss: () => void
}

/**
 * Auto-dismissing confirmation toast (STORY-102 AC4): a `role="status"` +
 * `aria-live="polite"` region — deliberately never `role="alert"`, which
 * would interrupt — so a screen reader announces the confirmation without
 * focus moving there (this component never calls `.focus()` on anything).
 * Used for plain success confirmations only ("Window scheduled" / "Window
 * deleted"); failures keep using the existing `role="alert"` patterns
 * already on the Maintenance form/page.
 *
 * The auto-dismiss timer restarts whenever `message` (or `duration`)
 * changes, so a second toast firing shortly after the first gets its own
 * full countdown instead of inheriting whatever was left of the previous
 * one's timer.
 */
export function Toast({ message, duration = 4000, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, duration)
    return () => window.clearTimeout(timer)
  }, [message, duration, onDismiss])

  return (
    <div className="toast" role="status" aria-live="polite">
      <span className="toast__message">{message}</span>
    </div>
  )
}
