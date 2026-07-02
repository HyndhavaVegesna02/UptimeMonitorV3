import { Button } from '../Button/Button'
import './ErrorState.css'

export interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

/** Error placeholder with an optional retry action (STORY-015a AC3/AC4).
 * `role="alert"` so the message is announced; the health "down" color marks
 * the icon only, never the text (AC6). */
export function ErrorState({
  message = 'Something went wrong',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="error-state">
      <p className="error-state__message" role="alert">
        <span className="error-state__icon" aria-hidden="true">
          ⚠
        </span>
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
