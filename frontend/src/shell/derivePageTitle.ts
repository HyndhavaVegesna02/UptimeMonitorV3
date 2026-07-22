import { matchPath } from 'react-router-dom'
import type { ComponentDTO } from '../api/types'
import { getTabByPath } from '../nav/tabs'

/**
 * The pattern for the component-scoped availability route (STORY-143 AC1) —
 * mirrors the `path="availability/:componentId"` entry `routes.tsx` registers
 * as a child of `ShellLayout`.
 */
const COMPONENT_AVAILABILITY_PATTERN = '/availability/:componentId'

/**
 * Derives the shell topbar's single `<h1>` title (STORY-121, extended
 * STORY-143 AC1) for a given route pathname. A static nav tab (e.g.
 * `/availability`) always wins via `getTabByPath`. The component-scoped
 * availability route (`/availability/:componentId`) has NO static tab entry
 * — its title is the matching component's own name (looked up in the SAME
 * `components` list `ShellLayout` already fetches for the Pinned sidebar
 * group/overall-status pill, so no extra fetch), falling back to the
 * `Availability` tab label while the components fetch hasn't resolved that id
 * yet (loading) or the id is genuinely unknown (the page's own body renders
 * the not-found treatment — the title just stays generic, never crashes).
 * Any other unmatched path falls back to `Dashboard`, matching the
 * `path="*"` redirect in `routes.tsx`.
 */
export function derivePageTitle(pathname: string, components: ComponentDTO[]): string {
  const tab = getTabByPath(pathname)
  if (tab) {
    return tab.label
  }

  const componentMatch = matchPath(COMPONENT_AVAILABILITY_PATTERN, pathname)
  if (componentMatch) {
    const componentId = componentMatch.params.componentId
    const component = components.find((candidate) => candidate.id === componentId)
    return component?.name ?? 'Availability'
  }

  return 'Dashboard'
}
