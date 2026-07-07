import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Icon } from '../components'
import { useApprovals } from '../features/approvals/useApprovals'
import { cx } from '../lib/cx'
import { TABS } from './tabs'
import './Sidebar.css'

const COLLAPSE_STORAGE_KEY = 'uptime-monitor-sidebar-collapsed'

/** Reads the persisted collapse preference; defaults to expanded (`false`)
 * whenever storage is unavailable or unset (private browsing, first visit,
 * or a test environment) — mirrors `resolveTheme.ts`'s defensive style. */
function readStoredCollapsed(): boolean {
  try {
    return window.localStorage.getItem(COLLAPSE_STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

function persistCollapsed(collapsed: boolean): void {
  try {
    window.localStorage.setItem(COLLAPSE_STORAGE_KEY, String(collapsed))
  } catch {
    // Storage disabled (private browsing) — the toggle still works for the
    // session, it just won't survive a reload.
  }
}

/**
 * Collapsible left icon sidebar (STORY-056 AC1, AC4/AC5) — replaces the old
 * top `Nav`. Logo+title header doubles as the collapse toggle
 * (`aria-expanded` + a dynamic accessible name); one real routed `NavLink`
 * per `TABS` entry (still the single nav source), each keeping an accessible
 * name via `aria-label` whether or not its text label is visually shown, so
 * collapsing to icons-only never leaves a link without a name. The
 * Approvals link additionally carries a live pending-count badge from
 * `useApprovals` — a dot while collapsed, the count while expanded — that
 * silently omits itself on a fetch failure or a zero count (AC4).
 */
export function Sidebar() {
  const [collapsed, setCollapsed] = useState<boolean>(() => readStoredCollapsed())
  const { state: approvalsState } = useApprovals()
  const pendingCount = approvalsState.phase === 'success' ? approvalsState.data.length : 0
  const showApprovalsBadge = pendingCount > 0

  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current
      persistCollapsed(next)
      return next
    })
  }

  return (
    <aside className={cx('sidebar', collapsed && 'sidebar--collapsed')}>
      <button
        type="button"
        className="sidebar__header"
        onClick={toggleCollapsed}
        aria-expanded={!collapsed}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <Icon name="logo" size={19} className="sidebar__logo" />
        {!collapsed && (
          <>
            <span className="sidebar__title">Uptime Monitor</span>
            <Icon name="chevron-left" size={15} className="sidebar__chevron" />
          </>
        )}
      </button>

      <nav className="sidebar__nav" aria-label="Primary">
        {TABS.map((tab) => {
          const isApprovals = tab.path === '/approvals'

          return (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.path === '/'}
              title={tab.label}
              className={({ isActive }) =>
                cx('sidebar__link', isActive && 'sidebar__link--active')
              }
            >
              <span className="sidebar__link-icon">
                <Icon name={tab.icon} size={16} />
                {isApprovals && showApprovalsBadge && collapsed && (
                  <span className="sidebar__badge-dot" aria-hidden="true" />
                )}
              </span>
              {/* The label is ALWAYS present for the accessible name (a
                  collapsed icon-only link must never lose its name) — only
                  its visibility toggles, via `.sr-only` when collapsed,
                  rather than swapping between two differently-worded nodes
                  (which would risk the two states drifting apart). */}
              <span className={cx('sidebar__link-label', collapsed && 'sr-only')}>
                {tab.label}
              </span>
              {!collapsed && isApprovals && showApprovalsBadge && (
                <span className="sidebar__badge-count" aria-hidden="true">
                  {pendingCount}
                </span>
              )}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
