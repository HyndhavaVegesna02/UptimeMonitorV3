import { CaretLineLeft, CaretLineRight, X } from '@phosphor-icons/react'
import { useEffect, useId } from 'react'
import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO } from '../../api/types'
import { Icon } from '../../components/Icon/Icon'
import { cx } from '../../lib/cx'
import { HEALTH_ICONS } from '../../lib/healthIcons'
import { NAV_GROUPS } from '../../nav/tabs'
import { TooltipGroupProvider } from '../TooltipGroupProvider'
import { useMediaQuery } from '../useMediaQuery'
import { NavItem } from './NavItem'
import './Sidebar.css'

/** Matches Sidebar.css's `@media (min-width: 861px)` desktop-rail breakpoint. */
const DESKTOP_QUERY = '(min-width: 861px)'

export interface SidebarProps {
  collapsed: boolean
  onToggleCollapsed: () => void
  activePath: string
  /** `GET /api/v1/approvals` array length (STORY-121 AC2) — 0 renders no badge. */
  approvalsCount: number
  /** `GET /api/v1/components` — sources the Pinned group's quick-links. */
  components: ComponentDTO[]
  /** Off-canvas sheet state (≤860px, AC6) — distinct from `collapsed`, which
   * only applies to the ≥861px desktop rail. */
  mobileOpen: boolean
  onCloseMobile: () => void
  /** The id the mobile sheet's `<aside>` renders under — `Topbar`'s
   * hamburger toggle points `aria-controls` at this same id, so the two
   * shell pieces must agree on it (`ShellLayout` generates one and passes
   * it to both). Falls back to an internally-generated id when Sidebar is
   * rendered standalone (e.g. in isolation tests). */
  navId?: string
}

const GROUP_LABELS: Record<string, string> = {
  monitoring: 'Monitoring',
  operations: 'Operations',
}

/**
 * The app's grouped sidebar nav (STORY-121 AC1/AC2/AC5/AC6): Monitoring +
 * Operations (the static six-route IA from `nav/tabs.ts`) plus a data-driven
 * Pinned group of component quick-links. Renders once; CSS (`Sidebar.css`)
 * switches its presentation between the expanded/rail desktop states and
 * the mobile off-canvas sheet at the story's breakpoints — `collapsed`
 * (rail) and `mobileOpen` (sheet) are independent, JS-tracked states so
 * behaviour (tooltips, Escape/backdrop dismissal) only activates for the
 * mode it belongs to.
 */
export function Sidebar({
  collapsed,
  onToggleCollapsed,
  activePath,
  approvalsCount,
  components,
  mobileOpen,
  onCloseMobile,
  navId: providedNavId,
}: SidebarProps) {
  const generatedNavId = useId()
  const navId = providedNavId ?? generatedNavId
  // The rail (icon-only + tooltip) presentation is a DESKTOP-only concept
  // (AC5); the mobile sheet always shows full labels (AC6) regardless of
  // the persisted desktop `collapsed` choice, so gate by real viewport too
  // — not just the `collapsed` boolean, which persists independent of
  // window size.
  const isDesktop = useMediaQuery(DESKTOP_QUERY)
  const railMode = collapsed && isDesktop

  useEffect(() => {
    if (!mobileOpen) {
      return
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onCloseMobile()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [mobileOpen, onCloseMobile])

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={onCloseMobile}
        />
      ) : null}
      <aside
        id={navId}
        className={cx(
          'shell-sidebar',
          collapsed && 'shell-sidebar--collapsed',
          mobileOpen && 'shell-sidebar--mobile-open',
        )}
      >
        {/* Mobile off-canvas sheet header only (STORY-141 AC2) — CSS-hidden
           on the ≥861px desktop rail/expanded presentations, matching the
           existing convention of always-rendering + CSS-gating visibility
           per breakpoint (e.g. `.shell-sidebar__toggle` below). Gives the
           drawer a brand/title landmark AND an explicit close affordance,
           in addition to the existing backdrop/Escape dismissal. */}
        <div className="shell-sidebar__mobile-header">
          <span className="shell-sidebar__brand">Uptime Monitor</span>
          <button
            type="button"
            className="shell-sidebar__mobile-close"
            aria-label="Close menu"
            onClick={onCloseMobile}
          >
            <Icon icon={X} aria-hidden size={18} />
          </button>
        </div>

        <button
          type="button"
          className="shell-sidebar__toggle"
          aria-expanded={!collapsed}
          aria-controls={navId}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          onClick={onToggleCollapsed}
        >
          <Icon icon={collapsed ? CaretLineRight : CaretLineLeft} aria-hidden size={16} />
        </button>

        <TooltipGroupProvider>
          {NAV_GROUPS.map((group) => (
            <nav key={group.id} className="shell-sidebar__group" aria-label={GROUP_LABELS[group.id]}>
              <h2 className="shell-sidebar__group-label">{group.label}</h2>
              <ul className="shell-sidebar__list">
                {group.tabs.map((tab) => (
                  <li key={tab.path}>
                    <NavItem
                      path={tab.path}
                      label={tab.label}
                      icon={tab.icon}
                      active={activePath === tab.path}
                      showTooltip={railMode}
                      badge={tab.path === '/approvals' ? approvalsCount : undefined}
                    />
                  </li>
                ))}
              </ul>
            </nav>
          ))}

          {components.length > 0 ? (
            <nav className="shell-sidebar__group" aria-label="Pinned">
              <h2 className="shell-sidebar__group-label">Pinned</h2>
              <ul className="shell-sidebar__list">
                {components.map((component) => (
                  <li key={component.id}>
                    <NavItem
                      path="/availability"
                      label={component.name}
                      icon={HEALTH_ICONS[toHealthStatus(component.status)]}
                      active={false}
                      showTooltip={railMode}
                    />
                  </li>
                ))}
              </ul>
            </nav>
          ) : null}
        </TooltipGroupProvider>
      </aside>
    </>
  )
}
