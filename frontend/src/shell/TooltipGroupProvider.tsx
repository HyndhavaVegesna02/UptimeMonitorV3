import type { ReactNode } from 'react'
import { useCallback, useRef, useState } from 'react'
import { TOOLTIP_GROUP_COOLDOWN_MS, TooltipGroupContext } from './tooltipGroupContext'

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
    }, TOOLTIP_GROUP_COOLDOWN_MS)
  }, [])

  return (
    <TooltipGroupContext.Provider value={{ warm, markShown, scheduleCooldown }}>
      {children}
    </TooltipGroupContext.Provider>
  )
}
