import type { ButtonHTMLAttributes } from 'react'
import { cx } from '../../lib/cx'
import './Button.css'

export type ButtonVariant = 'primary' | 'ghost' | 'danger'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  /** Shows a decorative spinner, sets `aria-busy`, and disables the button
   * (so it can't be re-triggered mid-request) while keeping its
   * accessible name unchanged — the label stays visible, never replaced
   * by the spinner alone. */
  loading?: boolean
}

/**
 * Primary/ghost/danger button primitive (STORY-103, Mission Teal v2 —
 * replaces the pre-rewrite primary/secondary/tertiary set). >=44px target
 * height (`--target-min`), tokens only. Defaults `type="button"` since
 * most uses in this app are actions, not form submits — pass
 * `type="submit"` explicitly where needed.
 */
export function Button({
  variant = 'primary',
  type = 'button',
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  const classes = cx('button', `button--${variant}`, className)

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <span className="button__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  )
}
