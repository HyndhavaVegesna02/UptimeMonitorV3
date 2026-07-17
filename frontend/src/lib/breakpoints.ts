/**
 * Shared responsive breakpoint values (STORY-096; journal D2 — Material
 * adaptive-navigation: rail at <=1024px, overlay drawer at <=768px). CSS
 * `@media` conditions cannot reference a CSS custom property (no browser
 * implements that without a preprocessor plugin, and sprint-52 froze new
 * dependencies mid-sprint — see the plan's "Tooling" note) — `tokens.css`'s
 * `--breakpoint-tablet`/`--breakpoint-mobile` mirror these same two numbers
 * for documentation and for any non-media-query CSS use. This module is the
 * single JS-side source of truth: `useMediaQuery`-based hooks (e.g.
 * `nav/useResponsiveSidebar.ts`) build their query strings from these
 * constants so the two breakpoints can never drift apart.
 */

export const BREAKPOINT_TABLET_MAX_PX = 1024
export const BREAKPOINT_MOBILE_MAX_PX = 768

/** Rail auto-collapse threshold (STORY-096 AC3). */
export const QUERY_TABLET_DOWN = `(max-width: ${BREAKPOINT_TABLET_MAX_PX}px)`

/** Overlay-drawer threshold (STORY-096 AC2). */
export const QUERY_MOBILE_DOWN = `(max-width: ${BREAKPOINT_MOBILE_MAX_PX}px)`
