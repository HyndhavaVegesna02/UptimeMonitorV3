import type { ReactNode } from 'react'
import './PageHeader.css'

export interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
}

/**
 * Shared page-level header (STORY-097 AC1) — the h1 + optional subtitle
 * every tab renders OUTSIDE its content card, with an optional actions slot
 * for page-level controls (e.g. Availability's legend + window switcher,
 * AC4). One `PageHeader` per route keeps exactly one h1 per page and a
 * sequential heading level (the card content below it defaults to `h2` via
 * `Panel`'s `headingLevel` prop).
 */
export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        <h1 className="text-h1 page-header__title">{title}</h1>
        {subtitle ? <p className="text-caption page-header__subtitle">{subtitle}</p> : null}
      </div>
      {actions ? <div className="page-header__actions">{actions}</div> : null}
    </div>
  )
}
