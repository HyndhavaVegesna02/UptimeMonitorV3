import { Icon } from '../components'
import './SampleModeBanner.css'

export interface SampleModeBannerProps {
  /** Whether the sample-mode-on warning should show. `AppShell` computes
   * this from the same lifted `useSampleMode()` result passed to `TopBar`
   * (`state.phase === 'success' && enabled === true`) — never a second,
   * independent hook call (see `TopBar.tsx`'s header comment for why that
   * would desync). */
  visible: boolean
  /** Whether the banner has been dismissed (STORY-102 AC2) — LIFTED to
   * `AppShell` via `useDismissibleBanner` (previously local state here) so
   * `TopBar`'s persistent "SAMPLE" chip can also read/drive it: the chip
   * renders exactly when `visible && dismissed`, and clicking it calls the
   * same `restore()` this banner's own dismiss button's opposite would. */
  dismissed: boolean
  /** Dismisses the banner (STORY-102: `AppShell`'s `useDismissibleBanner().dismiss`). */
  onDismiss: () => void
}

/**
 * Dismissible banner region under the top bar (STORY-056 AC3) showing the
 * sample-mode-on warning carried over verbatim from the old
 * `DashboardPage`'s inline `role="status"` text. Dismiss/re-arm state is
 * now CONTROLLED (STORY-102 AC2 — see `useDismissibleBanner`, which owns
 * the "re-arms once `visible` cycles false -> true" rule this component
 * used to implement internally); `AppShell` is the single source of truth
 * so `TopBar`'s persistent "SAMPLE" chip can observe the same state.
 */
export function SampleModeBanner({ visible, dismissed, onDismiss }: SampleModeBannerProps) {
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
        onClick={onDismiss}
      >
        Dismiss
      </button>
    </div>
  )
}
