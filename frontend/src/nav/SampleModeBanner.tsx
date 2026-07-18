import { Icon } from '../components'
import './SampleModeBanner.css'

export interface SampleModeBannerProps {
  /** Whether the sample-mode-on warning should show. `AppShell` computes
   * this from the same lifted `useSampleMode()` result passed to
   * `SampleModeSwitch` (`state.phase === 'success' && enabled === true`) —
   * never a second, independent hook call (see `AppShell.tsx`). */
  visible: boolean
  /** Whether the banner has been dismissed — LIFTED to `AppShell` via
   * `useDismissibleBanner` so the persistent "SAMPLE" chip can also
   * read/drive it: the chip renders exactly when `visible && dismissed`,
   * and clicking it calls the same `restore()` this banner's own dismiss
   * button's opposite would. */
  dismissed: boolean
  /** Dismisses the banner (`AppShell`'s `useDismissibleBanner().dismiss`). */
  onDismiss: () => void
}

/**
 * Dismissible banner region under the command bar (STORY-104 AC3, ported
 * verbatim from `ui-redesign` STORY-056/102 — salvage list) showing the
 * sample-mode-on warning. Dismiss/re-arm state is CONTROLLED (see
 * `useDismissibleBanner`) — `AppShell` is the single source of truth so the
 * persistent "SAMPLE" chip can observe the same state.
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
