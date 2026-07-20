import { Warning } from '@phosphor-icons/react'
import { Button } from '../Button/Button'
import { Icon } from '../Icon/Icon'
import './ErrorState.css'

export interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

/**
 * Error placeholder with an optional retry action (STORY-120 AC5).
 * `role="alert"` so the message is announced; the health "down" color marks
 * the icon only — the text itself is never color-coded (never color alone).
 */
export function ErrorState({ message = 'Something went wrong', onRetry }: ErrorStateProps) {
  return (
    <div className="error-state">
      <p className="error-state__message" role="alert">
        <Icon icon={Warning} aria-hidden className="error-state__icon" />
        {message}
      </p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  )
}
