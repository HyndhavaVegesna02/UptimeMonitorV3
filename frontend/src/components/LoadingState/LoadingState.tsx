import { cx } from '../../lib/cx'
import './LoadingState.css'

export interface LoadingStateProps {
  label?: string
  /** Renders the compact inline modifier (STORY-136 AC2) — no block
   * padding/centering, for tight spaces such as the topbar's overall-status
   * slot, in place of the default full-panel treatment. */
  compact?: boolean
}

/**
 * Loading placeholder (STORY-120 AC5). `role="status"` + a visible label so
 * assistive tech and sighted users both learn the surface is loading. The
 * spinner rotation is `prefers-reduced-motion`-guarded (LoadingState.css).
 */
export function LoadingState({ label = 'Loading…', compact = false }: LoadingStateProps) {
  return (
    <div className={cx('loading-state', compact && 'loading-state--compact')} role="status">
      <span className="loading-state__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
