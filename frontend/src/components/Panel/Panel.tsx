import type { HTMLAttributes, ReactNode } from 'react'
import './Panel.css'

export interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  children?: ReactNode
}

/**
 * Surface-1 panel with a hairline border and 12px radius (STORY-015a AC4) —
 * the base container every tab uses instead of copy-pasting the surface
 * treatment.
 */
export function Panel({ title, children, className, ...rest }: PanelProps) {
  const classes = ['panel', className].filter(Boolean).join(' ')

  return (
    <div className={classes} {...rest}>
      {title ? <h2 className="panel__title">{title}</h2> : null}
      {children}
    </div>
  )
}
