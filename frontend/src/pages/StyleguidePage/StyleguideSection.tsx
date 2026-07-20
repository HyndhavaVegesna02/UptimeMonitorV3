import type { ReactNode } from 'react'

export interface StyleguideSectionProps {
  title: string
  children?: ReactNode
}

/**
 * A labelled `<section role="region">` wrapper — every primitive gallery
 * entry on `/styleguide` is one of these, so each is independently
 * addressable by an accessible name in tests and for screen-reader users
 * jumping between landmarks.
 */
export function StyleguideSection({ title, children }: StyleguideSectionProps) {
  return (
    <section aria-label={title} className="styleguide-section">
      <h2 className="styleguide-section__title">{title}</h2>
      <div className="styleguide-section__body">{children}</div>
    </section>
  )
}
