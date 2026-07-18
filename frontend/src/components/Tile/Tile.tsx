import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import { cx } from '../../lib/cx'
import type { HealthStatus } from '../StatusBadge/StatusBadge'
import './Tile.css'

export type TileElevation = 'sm' | 'md' | 'lg'

interface TileOwnProps {
  children?: ReactNode
  className?: string
  /** Elevation level, mapped to the token shadow scale (border-glow in
   * dark / soft layered shadow in light). Defaults to 'md'. */
  elevation?: TileElevation
  /** An optional colored left-edge accent bar, keyed off the same 7-status
   * health vocabulary every other indicator in the app uses. */
  accent?: HealthStatus
  /** Renders the tile as a react-router `Link` to this path. */
  href?: LinkProps['to']
  /** Hover-scale (<=1.01) + focus-ring affordance. Defaults to `true`
   * whenever `href` or `onClick` is given (a tile is interactive the
   * moment it does something), `false` otherwise — pass explicitly to
   * override either default. */
  interactive?: boolean
}

export type TileProps = TileOwnProps &
  Omit<HTMLAttributes<HTMLDivElement> & ButtonHTMLAttributes<HTMLButtonElement>, keyof TileOwnProps>

/**
 * Bento-grid card primitive (STORY-103, Mission Teal — the base unit every
 * dashboard/availability/etc. rewrite composes from later stories).
 * Renders as:
 *  - a react-router `Link` when `href` is given (real anchor semantics,
 *    keyboard-navigable by default),
 *  - a `<button>` when `onClick` is given without `href` (so it is
 *    natively focusable/keyboard-activatable — never a `div` + onClick),
 *  - a plain `<div>` otherwise (a static, non-interactive container).
 * Hover scale is capped at 1.01 (brief: "no layout-shifting hovers") and
 * every interactive tile gets the shared two-tone focus ring.
 */
export function Tile({
  children,
  className,
  elevation = 'md',
  accent,
  href,
  interactive,
  onClick,
  ...rest
}: TileProps) {
  const isInteractive = interactive ?? (href != null || onClick != null)

  const classes = cx(
    'tile',
    `tile--elevation-${elevation}`,
    accent ? `tile--accent-${accent}` : null,
    isInteractive ? 'tile--interactive' : null,
    className,
  )

  if (href != null) {
    return (
      <Link to={href} className={classes} {...(rest as HTMLAttributes<HTMLAnchorElement>)}>
        {children}
      </Link>
    )
  }

  if (onClick != null) {
    return (
      <button
        type="button"
        className={classes}
        onClick={onClick}
        {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)}
      >
        {children}
      </button>
    )
  }

  return (
    <div className={classes} {...(rest as HTMLAttributes<HTMLDivElement>)}>
      {children}
    </div>
  )
}
