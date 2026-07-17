import { useState } from 'react'
import { QUERY_MOBILE_DOWN, QUERY_TABLET_DOWN } from '../lib/breakpoints'
import { useMediaQuery } from '../lib/useMediaQuery'
import { persistExpanded, resolveInitialExpanded } from './sidebarState'

export interface ResponsiveSidebar {
  /** Whether the sidebar renders as an overlay drawer (<=768px, STORY-096
   * AC2) instead of the persistent rail/expanded column. */
  isMobile: boolean
  /** Effective expanded/collapsed state for the persistent (non-drawer)
   * layout. */
  expanded: boolean
  toggleExpanded: () => void
  /** Overlay-drawer open state (only meaningful while `isMobile`) — closed
   * by default (STORY-096 AC2). */
  drawerOpen: boolean
  openDrawer: () => void
  closeDrawer: () => void
}

/**
 * Adaptive-shell state (STORY-096, journal D2 — Material adaptive
 * navigation): auto-collapses the sidebar to its existing icon rail at
 * <=1024px and tracks the mobile (<=768px) overlay-drawer's open/closed
 * state, on top of the pre-096 persisted expand/collapse preference
 * (`sidebarState.ts`, unchanged since STORY-056).
 *
 * The <=1024px rail is a NARROW-VIEWPORT OVERRIDE, not a persisted choice:
 * `preferenceExpanded` (backed by `localStorage`, exactly as before) always
 * holds the user's real intent, while `narrowOverride` is a same-viewport-
 * session escape hatch (AC3 "user can still expand") that resets to `null`
 * the moment the viewport widens back past 1024px — so re-widening always
 * reflects the persisted preference, never a temporary narrow-mode expand
 * (AC3, "user pref respected on re-widen"). Toggling while narrow therefore
 * never calls `persistExpanded` — only a toggle at desktop width does,
 * exactly the pre-096 contract.
 *
 * Both breakpoint-crossing resets below use the React-documented
 * "adjusting state when a prop changes" pattern (compare against a
 * mirrored previous-value state DURING render, not inside a `useEffect`) —
 * the same pattern `SampleModeBanner.tsx` and `useMediaQuery.ts` already
 * use, required here since `eslint-plugin-react-hooks`'s
 * `set-state-in-effect` rule (DoD gate) rejects a synchronous `setState`
 * call in an effect body.
 */
export function useResponsiveSidebar(): ResponsiveSidebar {
  const isNarrow = useMediaQuery(QUERY_TABLET_DOWN)
  const isMobile = useMediaQuery(QUERY_MOBILE_DOWN)

  const [preferenceExpanded, setPreferenceExpanded] = useState(() => resolveInitialExpanded())
  const [narrowOverride, setNarrowOverride] = useState<boolean | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const [prevIsNarrow, setPrevIsNarrow] = useState(isNarrow)
  if (isNarrow !== prevIsNarrow) {
    setPrevIsNarrow(isNarrow)
    if (!isNarrow) {
      setNarrowOverride(null)
    }
  }

  // The drawer never persists as "open" once its breakpoint no longer
  // applies (e.g. the viewport widens past 768px while it was open).
  const [prevIsMobile, setPrevIsMobile] = useState(isMobile)
  if (isMobile !== prevIsMobile) {
    setPrevIsMobile(isMobile)
    if (!isMobile) {
      setDrawerOpen(false)
    }
  }

  const expanded = isNarrow ? (narrowOverride ?? false) : preferenceExpanded

  const toggleExpanded = () => {
    if (isNarrow) {
      setNarrowOverride((current) => !(current ?? false))
      return
    }
    setPreferenceExpanded((current) => {
      const next = !current
      persistExpanded(next)
      return next
    })
  }

  return {
    isMobile,
    expanded,
    toggleExpanded,
    drawerOpen,
    openDrawer: () => setDrawerOpen(true),
    closeDrawer: () => setDrawerOpen(false),
  }
}
