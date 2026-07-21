import { useCallback, useState } from 'react'

/**
 * localStorage key for the desktop sidebar's expanded/collapsed choice
 * (STORY-121 AC5). Exported so tests can seed/assert the exact key the
 * pre-paint inline script (`index.html`) also reads.
 */
export const SIDEBAR_COLLAPSE_STORAGE_KEY = 'uptime-monitor:sidebar-collapsed'

function readStoredCollapsed(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY) === 'true'
  } catch {
    // Storage disabled (e.g. private browsing) — default to expanded.
    return false
  }
}

export interface UseSidebarCollapseResult {
  collapsed: boolean
  toggle: () => void
}

/**
 * Desktop sidebar collapse state (STORY-121 AC5): persisted to localStorage
 * and restored via a `useState` LAZY initializer, so the very first render
 * already reflects the stored choice — no post-mount flash of the wrong
 * state (rerender-lazy-state-init). `index.html`'s pre-paint inline script
 * reads the same `SIDEBAR_COLLAPSE_STORAGE_KEY` before React ever mounts, so
 * even the pre-hydration paint matches.
 */
export function useSidebarCollapse(): UseSidebarCollapseResult {
  const [collapsed, setCollapsed] = useState<boolean>(readStoredCollapsed)

  const toggle = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev
      try {
        window.localStorage.setItem(SIDEBAR_COLLAPSE_STORAGE_KEY, String(next))
      } catch {
        // Storage disabled — in-memory state still toggles for this session.
      }
      return next
    })
  }, [])

  return { collapsed, toggle }
}
