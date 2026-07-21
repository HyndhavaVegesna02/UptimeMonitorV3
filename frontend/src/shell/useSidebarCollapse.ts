import { useCallback, useLayoutEffect, useState } from 'react'

/**
 * localStorage key for the desktop sidebar's expanded/collapsed choice
 * (STORY-121 AC5). Exported so tests can seed/assert the exact key the
 * pre-paint inline script (`index.html`) also reads.
 */
export const SIDEBAR_COLLAPSE_STORAGE_KEY = 'uptime-monitor:sidebar-collapsed'

/**
 * The class `index.html`'s pre-paint inline script adds to `<html>` (before
 * React ever mounts) when the persisted choice is collapsed, so `Sidebar.css`
 * can render the correct rail width on the very first paint. Exported (same
 * pattern as `SIDEBAR_COLLAPSE_STORAGE_KEY`) so both `index.html`'s literal
 * string and this hook's cleanup below are provably the same class name
 * (`indexHtmlPrepaint.test.ts`).
 */
export const SIDEBAR_COLLAPSE_PREPAINT_CLASS = 'sidebar-collapsed-preload'

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

  // Quality-review CRITICAL fix: the pre-paint class must not outlive
  // hydration. `useLayoutEffect` runs synchronously after this render's DOM
  // mutations but BEFORE the browser paints, and by this point React has
  // already applied its own `.shell-sidebar--collapsed` class (from the same
  // `collapsed` value the pre-paint script read), which resolves to the
  // IDENTICAL rail width the pre-paint rule set — so removing the pre-paint
  // class here never changes what's on screen (no flash), but permanently
  // hands sole ownership of the width to React's class. Without this, the
  // pre-paint rule (`html.sidebar-collapsed-preload .shell-sidebar`, higher
  // specificity than `.shell-sidebar--collapsed` alone) would keep pinning
  // the sidebar at rail width even after clicking Expand.
  useLayoutEffect(() => {
    document.documentElement.classList.remove(SIDEBAR_COLLAPSE_PREPAINT_CLASS)
  }, [])

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
