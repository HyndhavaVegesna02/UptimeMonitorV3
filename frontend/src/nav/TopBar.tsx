import { Icon } from '../components'
import { cx } from '../lib/cx'
import { useTheme } from '../theme/useTheme'
import type { UseSampleModeResult } from '../features/dashboard/useSampleMode'
import './TopBar.css'

export interface TopBarProps {
  /** The LIFTED `useSampleMode()` result (owned by `AppShell`, shared with
   * `SampleModeBanner`) — never called independently here, so the trigger
   * and the banner can never disagree about the current flag/mutation
   * state (see `AppShell.tsx`). */
  sampleMode: UseSampleModeResult
}

/**
 * Top bar (STORY-056 AC2): right-aligned, `--header-height` tall. Hosts the
 * relocated sample-mode ⚡ trigger (still `role="switch"`/`aria-checked` —
 * the EXISTING `useSampleMode` contract, unchanged) and the theme toggle
 * carried over from the old `Nav`.
 */
export function TopBar({ sampleMode }: TopBarProps) {
  const { theme, toggleTheme } = useTheme()
  const { state, retry, enabled, setEnabled, mutating, mutationError } = sampleMode

  return (
    <header className="top-bar">
      {mutationError ? (
        <p role="alert" className="top-bar__error">
          {mutationError}
        </p>
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
        aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        title="Toggle theme"
      >
        <Icon name={theme === 'light' ? 'sun' : 'moon'} />
      </button>
    </header>
  )
}
