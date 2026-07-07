import type { IconName } from '../components'

/**
 * The six-tab information architecture (dossier §17, "two surfaces, not
 * one" — this is the internal dashboard's IA, carried forward from V2).
 * Single source of truth for both the sidebar (STORY-056) and AppShell
 * routing so they cannot drift out of sync. `icon` names the sidebar glyph
 * (STORY-055's shared `Icon` set) — kept here rather than in a parallel
 * lookup table so a new tab can never ship routed but iconless (or vice
 * versa).
 */
export interface TabDefinition {
  path: string
  label: string
  icon: IconName
}

export const TABS: readonly TabDefinition[] = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/availability', label: 'Availability', icon: 'availability' },
  { path: '/approvals', label: 'Approvals', icon: 'approvals' },
  { path: '/check-history', label: 'Check History', icon: 'history' },
  { path: '/maintenance', label: 'Maintenance', icon: 'maintenance' },
  { path: '/publications', label: 'Publications', icon: 'publications' },
]
