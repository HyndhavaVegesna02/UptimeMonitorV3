import type { Icon as PhosphorIcon, IconWeight } from '@phosphor-icons/react'
import { cx } from '../../lib/cx'

const DEFAULT_SIZE = 18
const DEFAULT_WEIGHT: IconWeight = 'regular'

type DecorativeProps = {
  /** Marks the icon as decorative — it MUST be paired with a visible text
   * label elsewhere (nav item text, StatusBadge label, button text). */
  'aria-hidden': true
  label?: undefined
}

type LabelledProps = {
  /** The icon IS the accessible name (e.g. a standalone icon-only button). */
  label: string
  'aria-hidden'?: undefined
}

export type IconProps = {
  /** A Phosphor icon component, e.g. `import { CheckCircle } from '@phosphor-icons/react'`. */
  icon: PhosphorIcon
  size?: number
  weight?: IconWeight
  className?: string
} & (DecorativeProps | LabelledProps)

/**
 * Thin Phosphor wrapper (STORY-120 AC1) pinning the app's default icon
 * size/weight. The type forces every call site to be explicit about
 * accessibility: either `aria-hidden` (decorative) or `label` (accessible
 * name) — there is no way to render an `<Icon>` that is silently neither.
 */
export function Icon({
  icon: Glyph,
  size = DEFAULT_SIZE,
  weight = DEFAULT_WEIGHT,
  className,
  label,
}: IconProps) {
  const a11yProps = label
    ? { role: 'img' as const, 'aria-label': label }
    : { 'aria-hidden': true as const }

  return <Glyph size={size} weight={weight} className={cx('icon', className)} {...a11yProps} />
}
