/**
 * Shared responsive breakpoint values (ported from `ui-redesign` STORY-096
 * — salvage list; journal D2 — adaptive navigation: rail/tab-bar collapse
 * at <=1024px, overlay sheet at <=768px, matching the ui-rewrite brief's
 * "390/768/1024/1440 all first-class"). CSS `@media` conditions cannot
 * reference a CSS custom property (no browser implements that without a
 * preprocessor plugin) — this module is the single JS-side source of truth:
 * `useMediaQuery`-based hooks build their query strings from these
 * constants so breakpoints used in JS and in CSS can never drift apart in
 * concept, even though CSS media queries must still hardcode the pixel
 * value on their own side.
 */

export const BREAKPOINT_TABLET_MAX_PX = 1024
export const BREAKPOINT_MOBILE_MAX_PX = 768

/** Tablet-and-down collapse threshold. */
export const QUERY_TABLET_DOWN = `(max-width: ${BREAKPOINT_TABLET_MAX_PX}px)`

/** Overlay-sheet threshold (the ≤768px hamburger sheet nav). */
export const QUERY_MOBILE_DOWN = `(max-width: ${BREAKPOINT_MOBILE_MAX_PX}px)`
