import type { ReactNode, SVGProps } from 'react'
import { cx } from '../../lib/cx'
import './Icon.css'

/**
 * Feather-style icon set (STORY-055 AC4) — the sidebar/nav/action glyphs the
 * sprint-38 Operator Dashboard redesign needs, path data taken verbatim from
 * `docs/scrum/sprints/2026-07-07-sprint-38/reference-operator-dashboard.dc.html`
 * so the rendered marks match the mock exactly.
 */
export type IconName =
  | 'logo'
  | 'dashboard'
  | 'availability'
  | 'approvals'
  | 'history'
  | 'maintenance'
  | 'publications'
  | 'chevron-left'
  | 'chevron-right'
  | 'sun'
  | 'moon'
  | 'alert-triangle'
  | 'check'
  | 'arrow-right'

const PATHS: Record<IconName, ReactNode> = {
  logo: <path d="M3 12h4l2 6 4-14 2 8h6" />,
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </>
  ),
  availability: <path d="M22 12h-4l-3 9L9 3l-3 9H2" />,
  approvals: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  history: <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />,
  maintenance: (
    <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z" />
  ),
  publications: <path d="M22 2 11 13M22 2l-7 20-4-9-9-4z" />,
  'chevron-left': <path d="M15 18l-6-6 6-6" />,
  'chevron-right': <path d="M9 6l6 6-6 6" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5" />
    </>
  ),
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
  'alert-triangle': (
    <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
  ),
  check: <path d="M20 6 9 17l-5-5" />,
  'arrow-right': <path d="M5 12h14M13 6l6 6-6 6" />,
}

export interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: number
  /**
   * Accessible name for a STANDALONE meaningful icon (renders `role="img"` +
   * a `<title>`). Omit for a decorative icon (the default — `aria-hidden`) —
   * every icon in this app that carries meaning is paired with a visible
   * text label elsewhere (nav item text, StatusBadge label, button text),
   * per the AC6 "never icon/color-only" invariant.
   */
  title?: string
}

/** Inline feather-style icon (STORY-055 AC4). Token-free by design — it
 * inherits `currentColor` from its context, so callers control color via
 * `color`/`var(--…)` on a wrapping/parent element, never a hardcoded fill. */
export function Icon({ name, size = 16, title, className, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cx('icon', className)}
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      {PATHS[name]}
    </svg>
  )
}
