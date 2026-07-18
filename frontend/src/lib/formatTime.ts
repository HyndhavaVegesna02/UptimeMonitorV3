import { useEffect, useState } from 'react'

/**
 * Human time formatting (ported from `ui-redesign` STORY-098, journal
 * decision D3, dossier §17 — salvage list, sprint-55 ui-rewrite brief): one
 * shared module for every "relative time" and "absolute local time" surface
 * in the app — no per-page reimplementation, no new date-library dependency
 * (hand-rolled against `Intl.*`). The contract: recency-oriented surfaces
 * (Check History, the Dashboard drill-down, Approvals, Publications) show
 * RELATIVE time ("4m ago" / "in 2h"); scheduling surfaces (Maintenance
 * windows) show ABSOLUTE LOCAL time with an explicit timezone label; the
 * raw ISO-UTC instant is ALWAYS available via a tooltip/`title` (never
 * lost) and callers additionally place it in a `<time dateTime=…>`
 * attribute. Invalid input NEVER crashes — every formatter falls back to
 * rendering the raw string it was given.
 */

const SECOND_MS = 1_000
const MINUTE_MS = 60 * SECOND_MS
const HOUR_MS = 60 * MINUTE_MS
const DAY_MS = 24 * HOUR_MS

/** How often a mounted `useRelativeTime` re-renders to keep "4m ago" moving
 * forward ("updates at least once a minute"). */
const TICK_INTERVAL_MS = MINUTE_MS

function isValidDate(date: Date): boolean {
  return !Number.isNaN(date.getTime())
}

/**
 * Relative time from `iso` to `now` (default the real current time) — the
 * PRIMARY recency-surface format. Floors to whole units so "4m ago" means
 * at least 4 full minutes have elapsed, matching the once-a-minute tick
 * cadence. Anything under a minute in either direction (including a few
 * seconds of clock skew putting a "past" event slightly in the future)
 * reads as "just now" rather than a jittery sub-minute count. Invalid
 * input renders the raw string unchanged — never throws.
 */
export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso)
  if (!isValidDate(date)) {
    return iso
  }

  const diffMs = now.getTime() - date.getTime()
  const absMs = Math.abs(diffMs)
  const future = diffMs < 0

  if (absMs < MINUTE_MS) {
    return 'just now'
  }
  if (absMs < HOUR_MS) {
    const minutes = Math.floor(absMs / MINUTE_MS)
    return future ? `in ${minutes}m` : `${minutes}m ago`
  }
  if (absMs < DAY_MS) {
    const hours = Math.floor(absMs / HOUR_MS)
    return future ? `in ${hours}h` : `${hours}h ago`
  }
  const days = Math.floor(absMs / DAY_MS)
  return future ? `in ${days}d` : `${days}d ago`
}

const ABSOLUTE_LOCAL_FORMAT: Intl.DateTimeFormatOptions = {
  dateStyle: 'medium',
  timeStyle: 'long',
}

/**
 * Absolute local time (locale-default, browser timezone), with the
 * timezone name spelled out (`timeStyle: 'long'`) — the scheduling-surface
 * format. Invalid input renders the raw string unchanged.
 */
export function formatAbsoluteLocal(iso: string): string {
  const date = new Date(iso)
  if (!isValidDate(date)) {
    return iso
  }
  return new Intl.DateTimeFormat(undefined, ABSOLUTE_LOCAL_FORMAT).format(date)
}

/**
 * The full tooltip/`title` text for a relative-time surface: the absolute
 * local time plus the raw ISO-UTC instant, so the exact original value is
 * always one hover away. Invalid input renders the raw string unchanged.
 */
export function formatTooltip(iso: string): string {
  const date = new Date(iso)
  if (!isValidDate(date)) {
    return iso
  }
  return `${formatAbsoluteLocal(iso)} · ${date.toISOString()} UTC`
}

const RANGE_TIME_FORMAT: Intl.DateTimeFormatOptions = {
  dateStyle: 'medium',
  timeStyle: 'short',
}
const TZ_NAME_FORMAT: Intl.DateTimeFormatOptions = {
  timeZoneName: 'short',
  hour: 'numeric',
}

export interface LocalRange {
  /** Local start–end range with a single trailing explicit timezone label
   * (e.g. "IST" / "GMT+5:30"), the primary display text. */
  text: string
  /** The raw UTC start–end range, for the tooltip/`title`. */
  tooltip: string
}

/**
 * A maintenance window's start–end range, rendered in the OPERATOR'S local
 * timezone with an explicit timezone label — the scheduling-surface
 * counterpart to `formatRelativeTime`. The raw UTC range is always
 * available via `.tooltip`. Invalid input on either side falls back to the
 * raw `start–end` string for both `.text` and `.tooltip`, never a crash.
 */
export function formatLocalRange(startIso: string, endIso: string): LocalRange {
  const start = new Date(startIso)
  const end = new Date(endIso)

  if (!isValidDate(start) || !isValidDate(end)) {
    const raw = `${startIso}–${endIso}`
    return { text: raw, tooltip: raw }
  }

  const dtf = new Intl.DateTimeFormat(undefined, RANGE_TIME_FORMAT)
  const tzName =
    new Intl.DateTimeFormat(undefined, TZ_NAME_FORMAT)
      .formatToParts(start)
      .find((part) => part.type === 'timeZoneName')?.value ?? ''

  const text = `${dtf.format(start)}–${dtf.format(end)}${tzName ? ` ${tzName}` : ''}`
  const tooltip = `${start.toISOString()} – ${end.toISOString()} UTC`
  return { text, tooltip }
}

export interface RelativeTimeParts {
  /** The relative-time display text, e.g. "4m ago" / "in 2h". */
  text: string
  /** The tooltip/`title` text — absolute local time + raw ISO-UTC. */
  title: string
}

/**
 * Render-ready relative time for one instant, ticking forward at least once
 * a minute while mounted. Pauses the tick while the document is hidden
 * (`visibilityState === 'hidden'`) — a backgrounded tab doesn't need to
 * keep re-rendering a label nobody is looking at; it catches up to the
 * correct value again on the next tick after it becomes visible.
 *
 * `now` is injectable (defaults to the real current time) so a test can
 * pass a fixed clock instead of depending on wall-clock time.
 */
export function useRelativeTime(iso: string, now: () => Date = () => new Date()): RelativeTimeParts {
  const [, setTick] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      if (typeof document === 'undefined' || document.visibilityState !== 'hidden') {
        setTick((value) => value + 1)
      }
    }, TICK_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  return {
    text: formatRelativeTime(iso, now()),
    title: formatTooltip(iso),
  }
}
