import { Icon } from '../components'
import { cx } from '../lib/cx'
import { useMediaQuery } from '../lib/useMediaQuery'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import type { UseSampleModeResult } from '../features/dashboard/useSampleMode'
import './SampleModeSwitch.css'

export interface SampleModeSwitchProps {
  /** The LIFTED `useSampleMode()` result (owned by `AppShell`, shared with
   * `SampleModeBanner`/the chip) — never called independently here, so the
   * switch and the banner can never disagree about the current
   * flag/mutation state (see `AppShell.tsx`). */
  sampleMode: UseSampleModeResult
}

/**
 * Sample-mode switch control (STORY-104 AC3, ported from `ui-redesign`
 * STORY-056/102's `TopBar` trigger — salvage list): `role="switch"` +
 * `aria-checked`, a visible "Sample mode" text label at desktop widths
 * (>=768px, `aria-hidden` since the `aria-label` already names it),
 * hidden at mobile widths to save space in the command bar. OFF is
 * NEUTRAL styling; ON is the warning/degraded accent — never red, which is
 * reserved for the genuine GET-failure retry affordance.
 */
export function SampleModeSwitch({ sampleMode }: SampleModeSwitchProps) {
  const { state, retry, enabled, setEnabled, mutating, mutationError } = sampleMode
  const isMobile = useMediaQuery(QUERY_MOBILE_DOWN)

  return (
    <div className="sample-mode-switch">
      {mutationError ? (
        <p role="alert" className="sample-mode-switch__error">
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
            'sample-mode-switch__toggle',
            enabled && 'sample-mode-switch__toggle--active',
          )}
          onClick={() => void setEnabled(!enabled)}
        >
          <Icon name="zap" />
          {!isMobile ? (
            <span className="sample-mode-switch__label" aria-hidden="true">
              Sample mode
            </span>
          ) : null}
        </button>
      ) : null}

      {state.phase === 'error' ? (
        <button
          type="button"
          className="sample-mode-switch__retry"
          onClick={retry}
          aria-label="Sample mode unavailable — retry"
          title="Sample mode unavailable — retry"
        >
          <Icon name="zap" />
        </button>
      ) : null}
    </div>
  )
}
