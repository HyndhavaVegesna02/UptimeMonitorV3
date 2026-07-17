import { describe, expect, it } from 'vitest'
import { formatLocalRange, formatRelativeTime, formatTooltip } from './formatTime'

const NOW = new Date('2026-07-17T12:00:00.000Z')

describe('formatRelativeTime', () => {
  it('renders "just now" for a timestamp under a minute old (AC2, D3)', () => {
    const thirtySecondsAgo = new Date(NOW.getTime() - 30_000).toISOString()
    expect(formatRelativeTime(thirtySecondsAgo, NOW)).toBe('just now')
  })

  it('renders "just now" for a timestamp a few seconds in the future (clock skew)', () => {
    const fewSecondsAhead = new Date(NOW.getTime() + 5_000).toISOString()
    expect(formatRelativeTime(fewSecondsAhead, NOW)).toBe('just now')
  })

  it('renders whole minutes ago', () => {
    const fourMinutesAgo = new Date(NOW.getTime() - 4 * 60_000).toISOString()
    expect(formatRelativeTime(fourMinutesAgo, NOW)).toBe('4m ago')
  })

  it('renders whole hours ago', () => {
    const twoHoursAgo = new Date(NOW.getTime() - 2 * 60 * 60_000).toISOString()
    expect(formatRelativeTime(twoHoursAgo, NOW)).toBe('2h ago')
  })

  it('renders whole days ago', () => {
    const threeDaysAgo = new Date(NOW.getTime() - 3 * 24 * 60 * 60_000).toISOString()
    expect(formatRelativeTime(threeDaysAgo, NOW)).toBe('3d ago')
  })

  it('renders a future minute offset as "in Xm"', () => {
    const fiveMinutesAhead = new Date(NOW.getTime() + 5 * 60_000).toISOString()
    expect(formatRelativeTime(fiveMinutesAhead, NOW)).toBe('in 5m')
  })

  it('renders a future hour offset as "in Xh"', () => {
    const twoHoursAhead = new Date(NOW.getTime() + 2 * 60 * 60_000).toISOString()
    expect(formatRelativeTime(twoHoursAhead, NOW)).toBe('in 2h')
  })

  it('renders a future day offset as "in Xd"', () => {
    const threeDaysAhead = new Date(NOW.getTime() + 3 * 24 * 60 * 60_000).toISOString()
    expect(formatRelativeTime(threeDaysAhead, NOW)).toBe('in 3d')
  })

  it('crosses the minute/hour boundary at exactly 60 minutes (non-aligned-boundary case)', () => {
    const exactlyOneHourAgo = new Date(NOW.getTime() - 60 * 60_000).toISOString()
    expect(formatRelativeTime(exactlyOneHourAgo, NOW)).toBe('1h ago')
  })

  it('crosses the hour/day boundary at exactly 24 hours', () => {
    const exactlyOneDayAgo = new Date(NOW.getTime() - 24 * 60 * 60_000).toISOString()
    expect(formatRelativeTime(exactlyOneDayAgo, NOW)).toBe('1d ago')
  })

  it('crosses the seconds/minute boundary at exactly 60 seconds', () => {
    const exactlyOneMinuteAgo = new Date(NOW.getTime() - 60_000).toISOString()
    expect(formatRelativeTime(exactlyOneMinuteAgo, NOW)).toBe('1m ago')
  })

  it('never crashes on invalid input — renders the raw string instead (AC1)', () => {
    expect(formatRelativeTime('not-a-real-date', NOW)).toBe('not-a-real-date')
    expect(formatRelativeTime('', NOW)).toBe('')
  })
})

describe('formatTooltip', () => {
  it('embeds the raw ISO-UTC instant so it is always available (AC1)', () => {
    const iso = '2026-07-17T13:29:17.931000Z'
    // Cannot assert the LOCAL portion without depending on the machine's
    // timezone, but the raw UTC instant must always be present verbatim.
    expect(formatTooltip(iso)).toContain(new Date(iso).toISOString())
  })

  it('never crashes on invalid input — renders the raw string instead (AC1)', () => {
    expect(formatTooltip('garbage')).toBe('garbage')
  })
})

describe('formatLocalRange', () => {
  it('renders a local time range with an explicit timezone label, and the raw UTC range in the tooltip (AC3)', () => {
    const startIso = '2026-07-07T10:00:00Z'
    const endIso = '2026-07-07T11:00:00Z'
    const start = new Date(startIso)
    const end = new Date(endIso)

    const dtf = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    const tzName =
      new Intl.DateTimeFormat(undefined, { timeZoneName: 'short', hour: 'numeric' })
        .formatToParts(start)
        .find((part) => part.type === 'timeZoneName')?.value ?? ''
    const expectedText = `${dtf.format(start)}–${dtf.format(end)}${tzName ? ` ${tzName}` : ''}`

    const result = formatLocalRange(startIso, endIso)
    expect(result.text).toBe(expectedText)
    expect(result.tooltip).toContain(start.toISOString())
    expect(result.tooltip).toContain(end.toISOString())
  })

  it('never crashes on invalid input — renders the raw strings instead (AC1)', () => {
    const result = formatLocalRange('garbage-start', 'garbage-end')
    expect(result.text).toBe('garbage-start–garbage-end')
    expect(result.tooltip).toBe('garbage-start–garbage-end')
  })
})
