import { useEffect, useState } from 'react'

/**
 * Hand-rolled `window.matchMedia` subscription hook (STORY-096) — no new
 * dependency needed for a single media-query listener, so the frozen-deps
 * constraint (sprint-52 plan, "Tooling") is met by rolling this ourselves.
 * Returns whether `query` currently matches, updating live as the
 * viewport/media state changes via the standard `change` event (the
 * `addListener`/`removeListener` pair this replaces is deprecated).
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query)
    setMatches(mediaQueryList.matches)

    function handleChange(event: MediaQueryListEvent) {
      setMatches(event.matches)
    }

    mediaQueryList.addEventListener('change', handleChange)
    return () => mediaQueryList.removeEventListener('change', handleChange)
  }, [query])

  return matches
}
