/**
 * The six-tab information architecture (dossier §17, "two surfaces, not
 * one" — this is the internal dashboard's IA, carried forward from V2).
 * Single source of truth for both Nav and AppShell routing so they cannot
 * drift out of sync.
 */
export interface TabDefinition {
  path: string
  label: string
}

export const TABS: readonly TabDefinition[] = [
  { path: '/', label: 'Dashboard' },
  { path: '/availability', label: 'Availability' },
  { path: '/approvals', label: 'Approvals' },
  { path: '/check-history', label: 'Check History' },
  { path: '/maintenance', label: 'Maintenance' },
  { path: '/publications', label: 'Publications' },
]
