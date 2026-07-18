import type { HealthStatus } from '../components'
import { Icon, RelativeTime } from '../components'
import type { UseSampleModeResult } from '../features/dashboard/useSampleMode'
import { useTheme } from '../theme/useTheme'
import { SampleModeChip } from './SampleModeChip'
import { SampleModeSwitch } from './SampleModeSwitch'
import { StatusDot } from './StatusDot'
import { TabNav } from './TabNav'
import './CommandBar.css'

export interface CommandBarProps {
  /** The worst-of overall status (STORY-104 AC2, `deriveOverallStatus`) —
   * `undefined` while the components fetch hasn't resolved yet. */
  overallStatus: HealthStatus | undefined
  /** The raw ISO instant of the most recent successful components fetch
   * (STORY-104 AC — "Updated Xs ago"); `undefined` before the first fetch
   * resolves, in which case nothing renders (no fabricated placeholder). */
  fetchedAtIso: string | undefined
  /** The LIFTED `useSampleMode()` result (owned by `AppShell`, shared with
   * the banner) — see `AppShell.tsx`'s header comment for why this is
   * never called independently here. */
  sampleMode: UseSampleModeResult
  /** `AppShell` computes this as "sample mode is ON AND the banner has
   * been dismissed" (`useDismissibleBanner`) — a single derived boolean,
   * so `CommandBar` never re-derives dismissal state itself. */
  showSampleChip: boolean
  /** Restores the dismissed `SampleModeBanner` — `AppShell` passes its
   * `useDismissibleBanner().restore`. */
  onRestoreBanner: () => void
}

/**
 * Slim top command bar (STORY-104 AC1, design brief §IA — replaces the
 * pre-rewrite left sidebar entirely): brand + live overall-status dot on
 * the left, the horizontal `TabNav` in the middle (CSS-hidden at <=768px,
 * replaced by a hamburger sheet trigger — STORY-104 Step 4), and a right
 * cluster of mode controls: the persistent "SAMPLE" chip (when shown), the
 * sample-mode switch, the theme toggle, and "Updated <RelativeTime>".
 */
export function CommandBar({
  overallStatus,
  fetchedAtIso,
  sampleMode,
  showSampleChip,
  onRestoreBanner,
}: CommandBarProps) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <header className="command-bar">
      <div className="command-bar__brand">
        <Icon name="logo" />
        <span className="command-bar__brand-text">Uptime Monitor</span>
        <StatusDot status={overallStatus} />
      </div>
      <TabNav className="command-bar__nav" />
      <div className="command-bar__cluster">
        {showSampleChip ? <SampleModeChip onRestore={onRestoreBanner} /> : null}
        <SampleModeSwitch sampleMode={sampleMode} />
        <button
          type="button"
          className="command-bar__theme-toggle"
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          <Icon name={isDark ? 'moon' : 'sun'} />
        </button>
        {fetchedAtIso ? (
          <span className="command-bar__updated">
            Updated <RelativeTime iso={fetchedAtIso} />
          </span>
        ) : null}
      </div>
    </header>
  )
}
