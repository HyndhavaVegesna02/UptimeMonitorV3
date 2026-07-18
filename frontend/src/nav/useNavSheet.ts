import { useState } from 'react'
import { QUERY_MOBILE_DOWN } from '../lib/breakpoints'
import { useMediaQuery } from '../lib/useMediaQuery'

export interface NavSheetState {
  /** Whether the tab nav renders as the mobile overlay sheet (<=768px,
   * STORY-104 AC4) instead of the persistent horizontal `TabNav`. */
  isMobile: boolean
  /** The sheet's open/closed state — closed by default. Only meaningful
   * while `isMobile`. */
  open: boolean
  openSheet: () => void
  closeSheet: () => void
}

/**
 * Adaptive-shell state for the mobile hamburger sheet (STORY-104 AC4,
 * design brief §IA — a simplified sibling of `ui-redesign`'s
 * `useResponsiveSidebar`: this shell has no rail/expand-collapse concept
 * to preserve, only the mobile <=768px sheet open/closed state).
 *
 * The sheet never persists as "open" once its breakpoint no longer
 * applies (e.g. the viewport widens past 768px while it was open) — uses
 * the React-documented "adjusting state when a prop changes" pattern
 * (compare against a mirrored previous-value state DURING render, not
 * inside a `useEffect`), the same pattern `useMediaQuery`/
 * `useDismissibleBanner` already use, required since
 * `eslint-plugin-react-hooks`'s `set-state-in-effect` rule (DoD gate)
 * rejects a synchronous `setState` call in an effect body.
 */
export function useNavSheet(): NavSheetState {
  const isMobile = useMediaQuery(QUERY_MOBILE_DOWN)
  const [open, setOpen] = useState(false)
  const [prevIsMobile, setPrevIsMobile] = useState(isMobile)

  if (isMobile !== prevIsMobile) {
    setPrevIsMobile(isMobile)
    if (!isMobile) {
      setOpen(false)
    }
  }

  return {
    isMobile,
    open,
    openSheet: () => setOpen(true),
    closeSheet: () => setOpen(false),
  }
}
