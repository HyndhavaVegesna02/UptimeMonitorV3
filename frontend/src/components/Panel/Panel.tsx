import type { HTMLAttributes, ReactNode } from 'react'
import { cx } from '../../lib/cx'
import './Panel.css'

export type PanelHeadingLevel = 'h1' | 'h2' | 'h3'

export interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  /** Defaults to "h2" (a nested/secondary panel). Each route's top-level
   * panel should pass "h1" so the page has exactly one level-one heading
   * (web-design-guidelines: "headings must be hierarchical"). */
  headingLevel?: PanelHeadingLevel
  children?: ReactNode
}

/**
 * Surface-1 panel with a hairline border and 12px radius (STORY-015a AC4) —
 * the base container every tab uses instead of copy-pasting the surface
 * treatment.
 */
export function Panel({
  title,
  headingLevel = 'h2',
  children,
  className,
  ...rest
}: PanelProps) {
  const classes = cx('panel', className)
  const Heading = headingLevel

  return (
    <div className={classes} {...rest}>
      {title ? <Heading className="panel__title">{title}</Heading> : null}
      {children}
    </div>
  )
}
