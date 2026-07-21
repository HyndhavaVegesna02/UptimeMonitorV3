import { useSyncExternalStore } from 'react'

function getSnapshot(query: string): () => boolean {
  return () => window.matchMedia(query).matches
}

function subscribe(query: string): (onStoreChange: () => void) => () => void {
  return (onStoreChange: () => void) => {
    const mediaQueryList = window.matchMedia(query)
    mediaQueryList.addEventListener('change', onStoreChange)
    return () => mediaQueryList.removeEventListener('change', onStoreChange)
  }
}

/**
 * Subscribes to a media query's live match state (STORY-121) — used to tell
 * the desktop collapsible rail (`min-width: 861px`) apart from the mobile
 * off-canvas sheet (`max-width: 860px`) in JS, not just CSS, so behaviour
 * (tooltips, Escape/backdrop dismissal, focus return) only applies at the
 * breakpoint it is meant for even as the viewport is resized live.
 *
 * `useSyncExternalStore` (not a manual `useEffect` + `setState`) is the
 * React-recommended way to subscribe to a browser API's external mutable
 * state — it also sidesteps the "setState synchronously in an effect"
 * lint rule a naive effect-based subscription would trip.
 */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(subscribe(query), getSnapshot(query))
}
