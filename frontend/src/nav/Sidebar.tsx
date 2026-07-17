import { NavLink } from 'react-router-dom'
import { Icon } from '../components'
import { cx } from '../lib/cx'
import { TABS } from './tabs'
import './Sidebar.css'

export interface SidebarProps {
  /** Expanded (labeled) vs. collapsed (icons-only) — persisted by the
   * caller (STORY-056 AC1; see `sidebarState.ts`). Ignored when
   * `variant="drawer"` (STORY-096 AC2), which always shows the full
   * labeled layout. */
  expanded: boolean
  onToggleExpanded: () => void
  /** Open-proposal count for the Approvals badge (STORY-056 AC4).
   * `undefined` while loading or on a fetch failure — no badge renders,
   * the graceful-degradation case. */
  pendingApprovals: number | undefined
  /** 'static' (default): the persistent rail/expanded sidebar — the header
   * toggles `expanded`/collapsed (STORY-056 AC1). 'drawer' (STORY-096 AC2):
   * rendered inside `SidebarDrawer`'s mobile overlay — always full-labeled,
   * and the header instead CLOSES the drawer (`onToggleExpanded` is the
   * drawer's close handler in this variant, not a collapse toggle). */
  variant?: 'static' | 'drawer'
  /** Called when a tab `NavLink` is activated (STORY-096 fix, 2026-07-17
   * reality-gate finding) — `SidebarDrawer` passes its `onClose` here so
   * navigating from the open drawer closes it instead of leaving it open
   * over the newly-navigated-to page. Omitted (no-op) for the static
   * rail/expanded usage, which has no drawer to close. */
  onNavigate?: () => void
}

/**
 * Collapsible left icon sidebar (STORY-056 AC1) replacing the old top
 * `Nav`. Every tab is a REAL routed `NavLink` — deliberately not an ARIA
 * tablist, same rationale as the nav it replaces (each is an
 * independently-addressable route). The visible label/badge text is
 * conditionally rendered per `expanded`, but every link's accessible name
 * is set explicitly via `aria-label` so it never changes shape between the
 * expanded and collapsed layouts (a screen-reader user gets "Approvals, 3
 * pending" either way; only the sighted, icon-only presentation changes).
 */
export function Sidebar({
  expanded,
  onToggleExpanded,
  pendingApprovals,
  variant = 'static',
  onNavigate,
}: SidebarProps) {
  const isDrawer = variant === 'drawer'
  // In the drawer variant the layout is always fully labeled — there is no
  // rail state inside an overlay drawer (STORY-096 AC2).
  const showLabels = isDrawer || expanded

  return (
    <aside
      className={cx(
        'sidebar',
        showLabels ? 'sidebar--expanded' : 'sidebar--collapsed',
        isDrawer && 'sidebar--drawer',
      )}
    >
      <button
        type="button"
        className="sidebar__header"
        onClick={onToggleExpanded}
        aria-expanded={isDrawer ? undefined : expanded}
        aria-label={
          isDrawer ? 'Close navigation' : expanded ? 'Collapse sidebar' : 'Expand sidebar'
        }
        title="Uptime Monitor"
      >
        <Icon name="logo" className="sidebar__logo" />
        {showLabels ? (
          <>
            <span className="sidebar__title">Uptime Monitor</span>
            <Icon
              name={isDrawer ? 'x' : 'chevron-left'}
              className="sidebar__collapse-icon"
            />
          </>
        ) : null}
      </button>

      <nav className="sidebar__nav" aria-label="Primary">
        {TABS.map((tab) => {
          const isApprovals = tab.path === '/approvals'
          const badgeCount = isApprovals ? pendingApprovals : undefined
          const hasBadge = typeof badgeCount === 'number' && badgeCount > 0
          const accessibleLabel = hasBadge
            ? `${tab.label}, ${badgeCount} pending`
            : tab.label

          return (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.path === '/'}
              title={tab.label}
              aria-label={accessibleLabel}
              onClick={onNavigate}
              className={({ isActive }) =>
                cx('sidebar__tab', isActive && 'sidebar__tab--active')
              }
            >
              <span className="sidebar__tab-icon-wrap">
                <Icon name={tab.icon} className="sidebar__tab-icon" />
                {hasBadge && !showLabels ? (
                  <span className="sidebar__badge-dot" aria-hidden="true" />
                ) : null}
              </span>
              {showLabels ? <span className="sidebar__tab-label">{tab.label}</span> : null}
              {hasBadge && showLabels ? (
                <span className="sidebar__badge" aria-hidden="true">
                  {badgeCount}
                </span>
              ) : null}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
