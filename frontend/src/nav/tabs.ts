import type { IconName } from '../components/Icon/Icon'

/**
 * The six-tab information architecture (dossier §17, "two surfaces, not
 * one" — this is the internal dashboard's IA, carried forward from V2).
 * Single source of truth for both the Sidebar and AppShell routing so they
 * cannot drift out of sync. `icon` was added at STORY-056 (sidebar redesign)
 * — still one definition per tab, consumed by both concerns.
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
