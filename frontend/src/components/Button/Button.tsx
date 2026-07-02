import type { ButtonHTMLAttributes } from 'react'
import './Button.css'

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

/**
 * Primary/secondary/tertiary button primitive (STORY-015a AC4). 8px radius,
 * >=40px target height, tokens only. Defaults `type="button"` since most
 * uses in this app are actions, not form submits — pass `type="submit"`
 * explicitly where needed.
 */
export function Button({
  variant = 'primary',
  type = 'button',
  className,
  ...rest
}: ButtonProps) {
  const classes = ['button', `button--${variant}`, className]
    .filter(Boolean)
    .join(' ')

  return <button type={type} className={classes} {...rest} />
}
