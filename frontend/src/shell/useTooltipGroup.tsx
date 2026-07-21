import type { ReactNode } from 'react'
import { createContext, useCallback, useContext, useRef, useState } from 'react'

/** How long the group stays "warm" (instant, no-delay tooltips) after the
 * last tooltip in it hides (emil-design-eng: "skip delay on subsequent
 * hovers" — once one tooltip is open, adjacent ones open instantly). */
const COOLDOWN_MS = 400

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

const TooltipGroupContext = createContext<TooltipGroupContextValue | undefined>(undefined)

const STANDALONE_VALUE: TooltipGroupContextValue = {
  warm: false,
  markShown: () => undefined,
  scheduleCooldown: () => undefined,
}

/**
 * Groups a set of tooltips (STORY-121 AC5 — the collapsed rail's nav-item
 * tooltips) so only the FIRST one in a hover session pays the opening delay;
 * every subsequent one (while the group is "warm") opens instantly. Wrap the
 * collapsed rail's nav list in this provider.
 */
export function TooltipGroupProvider({ children }: { children: ReactNode }) {
  const [warm, setWarm] = useState(false)
  const cooldownTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const markShown = useCallback(() => {
    if (cooldownTimer.current !== undefined) {
      clearTimeout(cooldownTimer.current)
      cooldownTimer.current = undefined
    }
    setWarm(true)
  }, [])

  const scheduleCooldown = useCallback(() => {
    cooldownTimer.current = setTimeout(() => {
      setWarm(false)
    }, COOLDOWN_MS)
  }, [])

  return (
    <TooltipGroupContext.Provider value={{ warm, markShown, scheduleCooldown }}>
      {children}
    </TooltipGroupContext.Provider>
  )
}

/**
 * Reads the enclosing `TooltipGroupProvider`. Outside one, returns a
 * standalone value that is never warm (a lone tooltip always uses its full
 * opening delay) so `Tooltip`/`NavItem` never need to guard against a
 * missing provider.
 */
export function useTooltipGroup(): TooltipGroupContextValue {
  const ctx = useContext(TooltipGroupContext)
  return ctx ?? STANDALONE_VALUE
}
