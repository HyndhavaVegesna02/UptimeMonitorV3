import { createContext, useContext } from 'react'

/** How long the group stays "warm" (instant, no-delay tooltips) after the
 * last tooltip in it hides (emil-design-eng: "skip delay on subsequent
 * hovers" — once one tooltip is open, adjacent ones open instantly). */
export const TOOLTIP_GROUP_COOLDOWN_MS = 400

export interface TooltipGroupContextValue {
  /** True once any tooltip in the group is showing, or briefly after one
   * hides (the cooldown window) — a newly-hovered tooltip in the group
   * should skip its opening delay while this is true. */
  warm: boolean
  /** Call when a tooltip in the group becomes visible. */
  markShown: () => void
  /** Call when a tooltip in the group hides — starts the cooldown countdown
   * back to "cold" (re-enabling the opening delay for the next tooltip). */
  scheduleCooldown: () => void
}

export const TooltipGroupContext = createContext<TooltipGroupContextValue | undefined>(undefined)

const STANDALONE_VALUE: TooltipGroupContextValue = {
  warm: false,
  markShown: () => undefined,
  scheduleCooldown: () => undefined,
}

/**
 * Reads the enclosing `TooltipGroupProvider`. Outside one, returns a
 * standalone value that is never warm (a lone tooltip always uses its full
 * opening delay) so `NavItem` never needs to guard against a missing
 * provider. Split into its own module (rather than living alongside
 * `TooltipGroupProvider`'s JSX) so `TooltipGroupProvider.tsx` exports only
 * the component (react-refresh/only-export-components).
 */
export function useTooltipGroup(): TooltipGroupContextValue {
  const ctx = useContext(TooltipGroupContext)
  return ctx ?? STANDALONE_VALUE
}
