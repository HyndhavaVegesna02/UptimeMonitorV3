import type { HTMLAttributes, ReactNode } from 'react'
import { cx } from '../../lib/cx'
import './Panel.css'

export type PanelHeadingLevel = 'h1' | 'h2' | 'h3'

export interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  /** Defaults to "h2" (a nested/secondary panel). Each route's top-level
   * panel should pass "h1" so the page has exactly one level-one heading. */
  headingLevel?: PanelHeadingLevel
  /** Adds the hover-lift affordance (translateY + stronger shadow) used by
   * the KPI cards — gated to fine-pointer hover devices in Panel.css. */
  interactive?: boolean
  children?: ReactNode
}

/**
 * The base surface primitive (STORY-120 AC5) — white card, hairline border,
 * 16px radius, whisper-soft shadow. Every panel/card in the app composes
 * this instead of re-declaring the surface treatment.
 */
export function Panel({
  title,
  headingLevel = 'h2',
  interactive = false,
  children,
  className,
  ...rest
}: PanelProps) {
  const Heading = headingLevel

  return (
    <div className={cx('panel', interactive && 'panel--interactive', className)} {...rest}>
      {title ? <Heading className="panel__title">{title}</Heading> : null}
      {children}
    </div>
  )
}
