import type { Icon as PhosphorIcon } from '@phosphor-icons/react'
import { useCallback, useId, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from '../../components/Icon/Icon'
import { cx } from '../../lib/cx'
import { useTooltipGroup } from '../tooltipGroupContext'
import './NavItem.css'

/** Opening delay before a COLD (not-yet-warm) tooltip appears — emil-design-eng
 * "tooltips delay before appearing to prevent accidental activation". */
const OPEN_DELAY_MS = 400

export interface NavItemProps {
  path: string
  label: string
  icon: PhosphorIcon
  active: boolean
  /** True in the collapsed desktop rail — renders an icon-only link with an
   * accessible hover/focus tooltip (STORY-121 AC5); false in the expanded
   * sidebar and the mobile sheet, where the label is always visible inline. */
  showTooltip: boolean
  /** Optional trailing badge (e.g. Approvals' pending count) — rendered
   * inline next to the label when expanded; omitted entirely in rail mode
   * (AC2 badge is a shell-level pending-count signal, not the rail's job). */
  badge?: number
}

/**
 * One sidebar nav link (STORY-121 AC1/AC2/AC5): a real `<Link>` (keyboard
 * navigable), `aria-current="page"` when active, and — in the collapsed
 * rail — a delayed, group-aware accessible tooltip showing the label
 * (emil-design-eng: first tooltip in a hover session is delayed, subsequent
 * ones in the same group are instant, via `useTooltipGroup`).
 */
export function NavItem({ path, label, icon, active, showTooltip, badge }: NavItemProps) {
  const tooltipId = useId()
  const [visible, setVisible] = useState(false)
  const [instant, setInstant] = useState(false)
  const openTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const { warm, markShown, scheduleCooldown } = useTooltipGroup()

  const clearOpenTimer = useCallback(() => {
    if (openTimer.current !== undefined) {
      clearTimeout(openTimer.current)
      openTimer.current = undefined
    }
  }, [])

  const show = useCallback(() => {
    if (!showTooltip) {
      return
    }
    if (warm) {
      setInstant(true)
      setVisible(true)
      markShown()
      return
    }
    clearOpenTimer()
    openTimer.current = setTimeout(() => {
      setInstant(false)
      setVisible(true)
      markShown()
    }, OPEN_DELAY_MS)
  }, [showTooltip, warm, markShown, clearOpenTimer])

  const hide = useCallback(() => {
    clearOpenTimer()
    setVisible(false)
    if (showTooltip) {
      scheduleCooldown()
    }
  }, [clearOpenTimer, showTooltip, scheduleCooldown])

  return (
    <span
      className={cx('nav-item', showTooltip && 'nav-item--rail')}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      <Link
        to={path}
        className={cx('nav-item__link', active && 'nav-item__link--active')}
        aria-current={active ? 'page' : undefined}
        aria-describedby={showTooltip && visible ? tooltipId : undefined}
      >
        <Icon icon={icon} aria-hidden className="nav-item__icon" />
        <span className="nav-item__label">{label}</span>
        {badge ? (
          <>
            <span className="nav-item__badge" aria-hidden="true">
              {badge}
            </span>
            {/* Quality-review MAJOR fix: the visible chip above is
               aria-hidden (its count is redundant once this text exists),
               so a screen-reader operator still learns the pending count —
               previously the link's accessible name was just "Approvals". */}
            <span className="sr-only">, {badge} pending</span>
          </>
        ) : null}
      </Link>
      {showTooltip && visible ? (
        <span id={tooltipId} role="tooltip" className={cx('nav-item__tooltip', instant && 'nav-item__tooltip--instant')}>
          {label}
          {badge ? ` (${badge})` : ''}
        </span>
      ) : null}
    </span>
  )
}
