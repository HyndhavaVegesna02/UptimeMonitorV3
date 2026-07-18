import { NavLink } from 'react-router-dom'
import { Icon } from '../components'
import { cx } from '../lib/cx'
import { TABS } from './tabs'
import './TabNav.css'

export interface TabNavProps {
  className?: string
  /** Called when a tab link is activated. `NavSheet` passes its own close
   * handler here so navigating from the open sheet closes it instead of
   * leaving it open over the destination page (the ported
   * `SidebarDrawer`/`onNavigate` fix). Omitted (no-op) for the desktop
   * bar, which has no sheet to close. */
  onNavigate?: () => void
}

/**
 * Horizontal tab nav (STORY-104 AC1, design brief §IA): the six routed
 * tabs, icon + visible label ALWAYS together (never icon-only in the top
 * bar, per the ui-ux-pro-max Navigation guideline) — used both in the
 * desktop command bar (CSS-hidden at <=768px) and, unchanged, inside the
 * mobile `NavSheet` (vertical layout via the `tab-nav--sheet` class
 * modifier). Every tab is a REAL routed `NavLink` (react-router
 * automatically sets `aria-current="page"` on the active one — AC1's
 * accessible active-route signal); the visible `tab-nav__tab--active`
 * class adds a teal underline + weight change so the active tab is never
 * indicated by color alone (ui-ux-pro-max Navigation guideline).
 */
export function TabNav({ className, onNavigate }: TabNavProps) {
  return (
    <nav className={cx('tab-nav', className)} aria-label="Primary">
      {TABS.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          end={tab.path === '/'}
          onClick={onNavigate}
          className={({ isActive }) => cx('tab-nav__tab', isActive && 'tab-nav__tab--active')}
        >
          <Icon name={tab.icon} className="tab-nav__icon" />
          <span className="tab-nav__label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
