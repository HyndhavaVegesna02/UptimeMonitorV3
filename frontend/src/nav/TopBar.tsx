import type { RefObject } from 'react'
import { Icon } from '../components'
import { cx } from '../lib/cx'
import { useTheme } from '../theme/useTheme'
import { useMediaQuery } from '../lib/useMediaQuery'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import type { UseSampleModeResult } from '../features/dashboard/useSampleMode'
import './TopBar.css'

export interface TopBarProps {
  /** The LIFTED `useSampleMode()` result (owned by `AppShell`, shared with
   * `SampleModeBanner`) — never called independently here, so the trigger
   * and the banner can never disagree about the current flag/mutation
   * state (see `AppShell.tsx`). */
  sampleMode: UseSampleModeResult
  /** STORY-096 AC2: renders the hamburger drawer trigger only at the
   * mobile (<=768px) breakpoint — `AppShell` derives this from the same
   * `useResponsiveSidebar().isMobile` the drawer itself reads, so the two
   * can never disagree about whether a drawer exists to open. */
  showMenuTrigger?: boolean
  onOpenMenu?: () => void
  /** Handed to `SidebarDrawer` as its `triggerRef` so focus can return here
   * on close. */
  menuTriggerRef?: RefObject<HTMLButtonElement | null>
  /** STORY-102 AC2: `AppShell` computes this as "sample mode is ON AND the
   * banner has been dismissed" — a single derived boolean, so `TopBar`
   * itself never re-derives dismissal state (see `useDismissibleBanner`). */
  showSampleChip?: boolean
  /** Restores the dismissed `SampleModeBanner` (STORY-102 AC2) — `AppShell`
   * passes its `useDismissibleBanner().restore`. */
  onRestoreBanner?: () => void
}

/**
 * Top bar (STORY-056 AC2): right-aligned, `--header-height` tall. Hosts the
 * relocated sample-mode ⚡ trigger (still `role="switch"`/`aria-checked` —
 * the EXISTING `useSampleMode` contract, unchanged) and the theme toggle
 * carried over from the old `Nav`.
 *
 * STORY-102 AC1 relabeled the trigger: a visible "Sample mode" text label
 * renders next to it at desktop widths (`!isMobile`, via the same
 * `useMediaQuery(QUERY_MOBILE_DOWN)` convention `useResponsiveSidebar` uses)
 * — the `aria-label` itself is unchanged/always-present, so the label is
 * purely a sighted-user affordance and is marked `aria-hidden` to avoid a
 * duplicate accessible-name announcement. OFF now renders with NEUTRAL
 * (`top-bar__button`-default) styling instead of red; ON renders the
 * warning/degraded accent (`top-bar__trigger--active`) — never red, which
 * is reserved for the genuine GET-failure `top-bar__trigger--error` variant.
 */
export function TopBar({
  sampleMode,
  showMenuTrigger = false,
  onOpenMenu,
  menuTriggerRef,
  showSampleChip = false,
  onRestoreBanner,
}: TopBarProps) {
  const { theme, toggleTheme } = useTheme()
  const { state, retry, enabled, setEnabled, mutating, mutationError } = sampleMode
  const isMobile = useMediaQuery(QUERY_MOBILE_DOWN)
  const themeToggleLabel = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'

  return (
    <header className="top-bar">
      {showMenuTrigger ? (
        <button
          type="button"
          ref={menuTriggerRef}
          className="top-bar__button top-bar__menu-trigger"
          onClick={onOpenMenu}
          aria-label="Open navigation menu"
          title="Open navigation menu"
        >
          <Icon name="menu" />
        </button>
      ) : null}

      {mutationError ? (
        <p role="alert" className="top-bar__error">
          {mutationError}
        </p>
      ) : null}

      {showSampleChip ? (
        <button
          type="button"
          className="top-bar__sample-chip"
          onClick={onRestoreBanner}
          aria-label="Sample mode is on — signals recorded as DOWN. Click to show details."
        >
          SAMPLE
        </button>
      ) : null}

      {state.phase === 'success' ? (
        <button
          type="button"
          role="switch"
          aria-checked={enabled ?? false}
          aria-label="Sample mode"
          title="Trigger test failure"
          disabled={mutating}
          className={cx(
            'top-bar__button',
            'top-bar__trigger',
            enabled && 'top-bar__trigger--active',
          )}
          onClick={() => void setEnabled(!enabled)}
        >
          <Icon name="zap" />
          {!isMobile ? (
            <span className="top-bar__trigger-label" aria-hidden="true">
              Sample mode
            </span>
          ) : null}
        </button>
      ) : null}

      {state.phase === 'error' ? (
        <button
          type="button"
          className="top-bar__button top-bar__trigger--error"
          onClick={retry}
          aria-label="Sample mode unavailable — retry"
          title="Sample mode unavailable — retry"
        >
          <Icon name="zap" />
        </button>
      ) : null}

      <button
        type="button"
        className="top-bar__button"
        onClick={toggleTheme}
        aria-label={themeToggleLabel}
        title={themeToggleLabel}
      >
        <Icon name={theme === 'light' ? 'sun' : 'moon'} />
      </button>
    </header>
  )
}
