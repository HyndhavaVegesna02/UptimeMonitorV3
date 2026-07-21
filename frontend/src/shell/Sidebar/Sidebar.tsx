import { CaretLineLeft, CaretLineRight } from '@phosphor-icons/react'
import { useEffect, useId } from 'react'
import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO } from '../../api/types'
import { Icon } from '../../components/Icon/Icon'
import { cx } from '../../lib/cx'
import { HEALTH_ICONS } from '../../lib/healthIcons'
import { NAV_GROUPS } from '../../nav/tabs'
import { TooltipGroupProvider } from '../useTooltipGroup'
import { NavItem } from './NavItem'
import './Sidebar.css'

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
}: SidebarProps) {
  const navId = useId()

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
                      showTooltip={collapsed}
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
                      showTooltip={collapsed}
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
