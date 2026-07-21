import { Wrench } from '@phosphor-icons/react'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { Icon } from '../../components/Icon/Icon'
import { Panel } from '../../components/Panel/Panel'
import type { MaintenanceWindowDTO } from '../../api/types'
import './MaintenancePanel.css'

export interface MaintenancePanelProps {
  windows: MaintenanceWindowDTO[]
}

const RANGE_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'UTC',
})

function formatWindow(startsAt: string, endsAt: string): string {
  const starts = new Date(startsAt)
  const ends = new Date(endsAt)
  const startParts = RANGE_FORMATTER.formatToParts(starts)
  const day = startParts.find((p) => p.type === 'month')!.value + ' ' + startParts.find((p) => p.type === 'day')!.value
  const startTime = `${startParts.find((p) => p.type === 'hour')!.value}:${startParts.find((p) => p.type === 'minute')!.value}`
  const endParts = RANGE_FORMATTER.formatToParts(ends)
  const endTime = `${endParts.find((p) => p.type === 'hour')!.value}:${endParts.find((p) => p.type === 'minute')!.value}`
  return `${day} · ${startTime}–${endTime} UTC`
}

/**
 * The Dashboard's upcoming-maintenance summary (STORY-122 AC4) — the
 * soonest scheduled window from `GET /api/v1/maintenance`, sourced by
 * `starts_at` (not array order). An empty list (the real captured sample)
 * renders a tidy `EmptyState`, never a blank panel.
 */
export function MaintenancePanel({ windows }: MaintenancePanelProps) {
  if (windows.length === 0) {
    return (
      <Panel title="Upcoming maintenance">
        <EmptyState message="No maintenance scheduled" detail="Nothing upcoming right now." />
      </Panel>
    )
  }

  const soonest = windows.reduce((earliest, window_) =>
    new Date(window_.starts_at) < new Date(earliest.starts_at) ? window_ : earliest,
  )
  const heading = soonest.title ?? soonest.reason ?? soonest.component_id

  return (
    <Panel title="Upcoming maintenance" className="maintenance-panel">
      <div className="maintenance-panel__row">
        <span className="maintenance-panel__icon" aria-hidden="true">
          <Icon icon={Wrench} aria-hidden size={17} />
        </span>
        <div>
          <div className="maintenance-panel__title">{heading}</div>
          {soonest.title && soonest.reason ? (
            <div className="maintenance-panel__reason">{soonest.reason}</div>
          ) : null}
          <div className="maintenance-panel__when">{formatWindow(soonest.starts_at, soonest.ends_at)}</div>
          <span className="maintenance-panel__tag">Scheduled</span>
        </div>
      </div>
    </Panel>
  )
}
