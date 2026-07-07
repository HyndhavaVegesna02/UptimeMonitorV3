import { NavLink } from 'react-router-dom'
import { Icon } from '../components'
import { cx } from '../lib/cx'
import { TABS } from './tabs'
import './Sidebar.css'

export interface SidebarProps {
  /** Expanded (labeled) vs. collapsed (icons-only) — persisted by the
   * caller (STORY-056 AC1; see `sidebarState.ts`). */
  expanded: boolean
  onToggleExpanded: () => void
  /** Open-proposal count for the Approvals badge (STORY-056 AC4).
   * `undefined` while loading or on a fetch failure — no badge renders,
   * the graceful-degradation case. */
  pendingApprovals: number | undefined
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
export function Sidebar({ expanded, onToggleExpanded, pendingApprovals }: SidebarProps) {
  return (
    <aside className={cx('sidebar', expanded ? 'sidebar--expanded' : 'sidebar--collapsed')}>
      <button
        type="button"
        className="sidebar__header"
        onClick={onToggleExpanded}
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
        title="Uptime Monitor"
      >
        <Icon name="logo" className="sidebar__logo" />
        {expanded ? (
          <>
            <span className="sidebar__title">Uptime Monitor</span>
            <Icon name="chevron-left" className="sidebar__collapse-icon" />
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
              className={({ isActive }) =>
                cx('sidebar__tab', isActive && 'sidebar__tab--active')
              }
            >
              <span className="sidebar__tab-icon-wrap">
                <Icon name={tab.icon} className="sidebar__tab-icon" />
                {hasBadge && !expanded ? (
                  <span className="sidebar__badge-dot" aria-hidden="true" />
                ) : null}
              </span>
              {expanded ? <span className="sidebar__tab-label">{tab.label}</span> : null}
              {hasBadge && expanded ? (
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
