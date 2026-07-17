import { useEffect, useState } from 'react'

/**
 * Hand-rolled `window.matchMedia` subscription hook (ported from
 * `ui-redesign` STORY-096 — salvage list). Returns whether `query`
 * currently matches, updating live as the viewport/media state changes via
 * the standard `change` event (the `addListener`/`removeListener` pair
 * this replaces is deprecated).
 *
 * Re-evaluating `matches` when `query` itself changes uses the
 * React-documented "adjusting state when a prop changes" pattern (compare
 * against a mirrored previous-value state DURING render, not inside a
 * `useEffect`) — required since `eslint-plugin-react-hooks`'s
 * `set-state-in-effect` rule (DoD gate) rejects a synchronous `setState`
 * in an effect body.
 */
export function useMediaQuery(query: string): boolean {
  const [trackedQuery, setTrackedQuery] = useState(query)
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)

  if (query !== trackedQuery) {
    setTrackedQuery(query)
    setMatches(window.matchMedia(query).matches)
  }

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query)

    function handleChange(event: MediaQueryListEvent) {
      setMatches(event.matches)
    }

    mediaQueryList.addEventListener('change', handleChange)
    return () => mediaQueryList.removeEventListener('change', handleChange)
  }, [query])

  return matches
}
