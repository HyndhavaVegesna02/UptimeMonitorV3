import { Bell, List, Plus } from '@phosphor-icons/react'
import type { RefObject } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../../components/Button/Button'
import { Icon } from '../../components/Icon/Icon'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { HEALTH_ICONS } from '../../lib/healthIcons'
import { formatLastUpdated } from './formatLastUpdated'
import './Topbar.css'

export interface TopbarProps {
  title: string
  overallStatus: HealthStatus
  lastUpdated: Date | null
  /** Injected "now" so relative-time rendering stays deterministic/testable
   * — never `Date.now()` read directly inside the component. */
  now: Date
  mobileNavOpen: boolean
  mobileNavId: string
  onOpenMobileNav: () => void
  mobileToggleRef: RefObject<HTMLButtonElement | null>
}

/**
 * The shell's topbar (STORY-121 AC3): page title, the worst-of overall
 * status pill (dot + icon + text — never colour alone, StatusBadge AC3),
 * a last-updated indicator, a notifications button, and the "＋ Maintenance"
 * affordance. Also hosts the mobile off-canvas sheet's hamburger toggle
 * (AC6) — a button distinct from the desktop rail's collapse toggle
 * (`Sidebar.tsx`), only visible at the ≤860px breakpoint (`Topbar.css`).
 */
export function Topbar({
  title,
  overallStatus,
  lastUpdated,
  now,
  mobileNavOpen,
  mobileNavId,
  onOpenMobileNav,
  mobileToggleRef,
}: TopbarProps) {
  return (
    <header className="shell-topbar">
      <div className="shell-topbar__leading">
        <button
          type="button"
          ref={mobileToggleRef}
          className="shell-topbar__mobile-toggle"
          aria-expanded={mobileNavOpen}
          aria-controls={mobileNavId}
          aria-label="Navigation menu"
          onClick={onOpenMobileNav}
        >
          <Icon icon={List} aria-hidden size={20} />
        </button>
        <h1 className="shell-topbar__title">{title}</h1>
        <StatusBadge status={overallStatus} icon={HEALTH_ICONS[overallStatus]} />
      </div>

      <div className="shell-topbar__trailing">
        <span className="shell-topbar__last-updated">{formatLastUpdated(lastUpdated, now)}</span>
        <Link to="/maintenance" className="button button--secondary shell-topbar__maintenance">
          <Icon icon={Plus} aria-hidden size={16} />
          {/* Visually hidden (not aria-hidden) below 480px — the link's
             accessible name stays "Maintenance" even icon-only, avoiding a
             horizontal-scroll-causing label at the narrowest phone widths
             (ui-ux-pro-max: Horizontal Scroll, High severity). */}
          <span className="shell-topbar__maintenance-label">Maintenance</span>
        </Link>
        <Button variant="ghost" iconOnly aria-label="Notifications">
          <Icon icon={Bell} aria-hidden />
        </Button>
      </div>
    </header>
  )
}
