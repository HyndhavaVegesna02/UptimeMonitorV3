import { useEffect, useState } from 'react'
import { Icon } from '../components'
import './SampleModeBanner.css'

export interface SampleModeBannerProps {
  /** Whether the sample-mode-on warning should show. `AppShell` computes
   * this from the same lifted `useSampleMode()` result passed to `TopBar`
   * (`state.phase === 'success' && enabled === true`) — never a second,
   * independent hook call (see `TopBar.tsx`'s header comment for why that
   * would desync). */
  visible: boolean
}

/**
 * Dismissible banner region under the top bar (STORY-056 AC3) showing the
 * sample-mode-on warning carried over verbatim from the old
 * `DashboardPage`'s inline `role="status"` text. Dismissing is LOCAL,
 * session-scoped UI state — it resets (the banner is ready to show again)
 * the next time `visible` transitions false -> true, so toggling sample
 * mode off and back on always re-surfaces the warning.
 */
export function SampleModeBanner({ visible }: SampleModeBannerProps) {
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (visible) {
      setDismissed(false)
    }
  }, [visible])

  if (!visible || dismissed) {
    return null
  }

  return (
    <div className="sample-mode-banner" role="status">
      <Icon name="alert-triangle" className="sample-mode-banner__icon" />
      <span className="sample-mode-banner__text">
        sample mode — signals recorded as DOWN
      </span>
      <button
        type="button"
        className="sample-mode-banner__dismiss"
        onClick={() => setDismissed(true)}
      >
        Dismiss
      </button>
    </div>
  )
}
