import {
  CheckCircle,
  ClockCounterClockwise,
  Gauge,
  Megaphone,
  SquaresFour,
  Wrench,
} from '@phosphor-icons/react'
import type { Icon as PhosphorIcon } from '@phosphor-icons/react'

export type NavGroupId = 'monitoring' | 'operations'

export interface NavTab {
  path: string
  label: string
  icon: PhosphorIcon
  group: NavGroupId
}

export interface NavGroup {
  id: NavGroupId
  label: string
  tabs: NavTab[]
}

/**
 * The six-route IA (STORY-121 AC1), grouped per the approved prototype
 * (docs/scrum/sprints/2026-07-18-ui-prototyping/round-2-refimg-system.md):
 * MONITORING {Dashboard, Availability, History} / OPERATIONS {Approvals,
 * Maintenance, Publications}. `Sidebar` renders these two groups plus a
 * third, data-driven "Pinned" group (component quick-links — not a static
 * tab, so it lives in `Sidebar` itself). `ShellLayout` derives the topbar
 * page title from this same table via `getTabByPath`.
 */
export const NAV_GROUPS: NavGroup[] = [
  {
    id: 'monitoring',
    label: 'Monitoring',
    tabs: [
      { path: '/dashboard', label: 'Dashboard', icon: SquaresFour, group: 'monitoring' },
      { path: '/availability', label: 'Availability', icon: Gauge, group: 'monitoring' },
      { path: '/history', label: 'History', icon: ClockCounterClockwise, group: 'monitoring' },
    ],
  },
  {
    id: 'operations',
    label: 'Operations',
    tabs: [
      { path: '/approvals', label: 'Approvals', icon: CheckCircle, group: 'operations' },
      { path: '/maintenance', label: 'Maintenance', icon: Wrench, group: 'operations' },
      { path: '/publications', label: 'Publications', icon: Megaphone, group: 'operations' },
    ],
  },
]

export const ALL_TABS: NavTab[] = NAV_GROUPS.flatMap((group) => group.tabs)

export function getTabByPath(pathname: string): NavTab | undefined {
  return ALL_TABS.find((tab) => tab.path === pathname)
}
