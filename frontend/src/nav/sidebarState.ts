/**
 * Sidebar collapse-state persistence (STORY-056 AC1). Mirrors
 * `theme/resolveTheme.ts`'s pattern (a dedicated storage key, a resolver
 * read once at mount, a setter called from the toggle handler) so the
 * sidebar's expanded/collapsed choice survives a reload the same way the
 * theme override does. Defaults to expanded (`true`) — a fresh visitor
 * sees the full labeled sidebar, matching the mock's default state.
 */

export const SIDEBAR_STORAGE_KEY = 'uptime-monitor-sidebar-expanded'

/** The persisted choice, or the `true` (expanded) default when nothing is
 * stored or the stored value is not one of the two literal strings this
 * module writes. */
export function resolveInitialExpanded(): boolean {
  const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
  if (stored === 'false') {
    return false
  }
  return true
}

/** Persist an explicit user choice. */
export function persistExpanded(expanded: boolean): void {
  window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(expanded))
}
