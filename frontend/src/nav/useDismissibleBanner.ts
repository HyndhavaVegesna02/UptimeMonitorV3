import { useState } from 'react'

export interface DismissibleBanner {
  dismissed: boolean
  dismiss: () => void
  restore: () => void
}

/**
 * Lifts the `SampleModeBanner`'s dismiss/re-arm state OUT of the banner
 * component itself (ported from `ui-redesign` STORY-102 AC2, salvage list)
 * so `CommandBar` can also read `dismissed` — to decide whether the
 * persistent "SAMPLE" chip should render — and restore the banner from the
 * chip's click handler.
 *
 * Re-arms (resets `dismissed` back to `false`) whenever `visible`
 * transitions `false -> true` — toggling sample mode off then back on
 * always re-surfaces the banner, even if it was dismissed on a prior ON
 * cycle. Uses the React-documented "adjusting state when a prop changes"
 * pattern (compare against a mirrored previous-value state DURING render,
 * not inside a `useEffect`) — the same pattern `useMediaQuery` and the
 * STORY-104 `useComponents` fetchedAt tracking use, required since
 * `eslint-plugin-react-hooks`'s `set-state-in-effect` rule (DoD gate)
 * rejects a synchronous `setState` call in an effect body.
 */
export function useDismissibleBanner(visible: boolean): DismissibleBanner {
  const [dismissed, setDismissed] = useState(false)
  const [prevVisible, setPrevVisible] = useState(visible)

  if (visible !== prevVisible) {
    setPrevVisible(visible)
    if (visible) {
      setDismissed(false)
    }
  }

  return {
    dismissed,
    dismiss: () => setDismissed(true),
    restore: () => setDismissed(false),
  }
}
