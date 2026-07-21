import { useEffect, useState } from 'react'

/**
 * Subscribes to a media query's live match state (STORY-121) — used to tell
 * the desktop collapsible rail (`min-width: 861px`) apart from the mobile
 * off-canvas sheet (`max-width: 860px`) in JS, not just CSS, so behaviour
 * (tooltips, Escape/backdrop dismissal, focus return) only applies at the
 * breakpoint it is meant for even as the viewport is resized live.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query)
    setMatches(mediaQueryList.matches)

    function handleChange(event: MediaQueryListEvent | { matches: boolean }) {
      setMatches(event.matches)
    }

    mediaQueryList.addEventListener('change', handleChange as (event: MediaQueryListEvent) => void)
    return () => {
      mediaQueryList.removeEventListener(
        'change',
        handleChange as (event: MediaQueryListEvent) => void,
      )
    }
  }, [query])

  return matches
}
