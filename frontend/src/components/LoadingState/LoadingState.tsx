import './LoadingState.css'

export interface LoadingStateProps {
  label?: string
}

/** Loading placeholder (STORY-015a AC4). `role="status"` + visible label so
 * assistive tech and sighted users both learn the surface is loading. */
export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
