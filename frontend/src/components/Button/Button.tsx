import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cx } from '../../lib/cx'
import './Button.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'

type IconOnlyProps = {
  iconOnly: true
  'aria-label': string
  children?: ReactNode
}

type LabelledProps = {
  iconOnly?: false
  'aria-label'?: string
  children: ReactNode
}

export type ButtonProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  'type' | 'children' | 'aria-label'
> & {
  variant?: ButtonVariant
} & (IconOnlyProps | LabelledProps)

/**
 * The base pressable primitive (STORY-120 AC5). `type="button"` by default
 * so it never accidentally submits a surrounding form. `:active` scale +
 * `:focus-visible` ring per emil-design-eng/web-interface-guidelines; the
 * press-scale animates only `transform` and is guarded by
 * `prefers-reduced-motion` (Button.css).
 */
export function Button({
  variant = 'primary',
  iconOnly = false,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cx('button', `button--${variant}`, iconOnly && 'button--icon-only', className)}
      {...rest}
    />
  )
}
