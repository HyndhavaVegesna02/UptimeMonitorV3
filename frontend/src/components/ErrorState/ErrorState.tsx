import { Button } from '../Button/Button'
import { Icon } from '../Icon/Icon'
import './ErrorState.css'

export interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

/** Error placeholder with an optional retry action (STORY-015a AC3/AC4;
 * icon restyled to the shared feather-style `Icon` set at STORY-055).
 * `role="alert"` so the message is announced; the health "down" color marks
 * the icon only, never the text (AC6). */
export function ErrorState({
  message = 'Something went wrong',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="error-state">
      <p className="error-state__message" role="alert">
        <Icon name="alert-triangle" className="error-state__icon" />
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
