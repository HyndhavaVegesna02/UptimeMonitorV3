import './LoadingState.css'

export interface LoadingStateProps {
  label?: string
}

/**
 * Loading placeholder (STORY-120 AC5). `role="status"` + a visible label so
 * assistive tech and sighted users both learn the surface is loading. The
 * spinner rotation is `prefers-reduced-motion`-guarded (LoadingState.css).
 */
export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
