import { describe, expect, it } from 'vitest'
import { fieldErrorFromDetail, validateMaintenanceForm } from './fieldError'

describe('fieldErrorFromDetail', () => {
  it('maps the empty-component_id detail message to "component_id" (AC3)', () => {
    expect(fieldErrorFromDetail('component_id must be a non-empty string.')).toBe(
      'component_id',
    )
  })

  it('maps a naive starts_at detail message to "starts_at" (AC3)', () => {
    expect(fieldErrorFromDetail('starts_at must be timezone-aware.')).toBe('starts_at')
  })

  it('maps a naive ends_at detail message to "ends_at" (AC3)', () => {
    expect(fieldErrorFromDetail('ends_at must be timezone-aware.')).toBe('ends_at')
  })

  it('maps the domain-layer starts_at wording variant to "starts_at" too', () => {
    expect(fieldErrorFromDetail('starts_at must be a tz-aware UTC datetime')).toBe(
      'starts_at',
    )
  })

  it('returns null for a detail message naming none of the three fields', () => {
    expect(fieldErrorFromDetail('Internal server error')).toBeNull()
  })

  it('returns null when detail is undefined (non-422 failure)', () => {
    expect(fieldErrorFromDetail(undefined)).toBeNull()
  })

  it('maps the ordering-error detail message to "ends_at", not "starts_at" (STORY-052 AC2)', () => {
    expect(
      fieldErrorFromDetail('ends_at must be strictly greater than starts_at.'),
    ).toBe('ends_at')
  })

  it('resolves a detail naming several fields deterministically and never throws (STORY-052 AC2)', () => {
    // The raw Pydantic ValidationError blob this guards against: its
    // `input_value={...}` echo contains a `component_id` token ahead of the
    // `ends_at`/`starts_at` mention in the message, which is exactly the
    // mis-mapping this story fixes for the clean ordering message. Any
    // detail naming multiple fields must resolve to a single, deterministic
    // field and must never throw.
    const multiFieldDetail =
      "1 validation error for MaintenanceWindow\n  Value error, ends_at must be strictly greater than starts_at [type=value_error, input_value={'component_id': 'checkout', 'starts_at': ..., 'ends_at': ...}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/value_error"

    expect(() => fieldErrorFromDetail(multiFieldDetail)).not.toThrow()
    const first = fieldErrorFromDetail(multiFieldDetail)
    const second = fieldErrorFromDetail(multiFieldDetail)
    expect(first).toBe(second)
    expect(['component_id', 'starts_at', 'ends_at']).toContain(first)
  })
})

describe('validateMaintenanceForm (STORY-102 AC4 — client-side, pre-submit)', () => {
  const VALID = {
    title: 'Routine check',
    componentId: 'sockshop-frontend',
    startsAt: '2026-07-09T09:00',
    endsAt: '2026-07-09T10:00',
  }

  it('returns no errors for a fully valid, well-ordered form', () => {
    expect(validateMaintenanceForm(VALID)).toEqual([])
  })

  it('reports Title required when blank/whitespace-only', () => {
    expect(validateMaintenanceForm({ ...VALID, title: '   ' })).toEqual([
      { field: 'title', message: 'Title is required.' },
    ])
  })

  it('reports Component required when blank', () => {
    expect(validateMaintenanceForm({ ...VALID, componentId: '' })).toEqual([
      { field: 'component_id', message: 'Component is required.' },
    ])
  })

  it('reports Start required when blank', () => {
    expect(validateMaintenanceForm({ ...VALID, startsAt: '' })).toEqual([
      { field: 'starts_at', message: 'Start is required.' },
    ])
  })

  it('reports End required when blank', () => {
    expect(validateMaintenanceForm({ ...VALID, endsAt: '' })).toEqual([
      { field: 'ends_at', message: 'End is required.' },
    ])
  })

  it('orders multiple failures Title -> Component -> Start -> End (for "focus first invalid")', () => {
    const errors = validateMaintenanceForm({
      title: '',
      componentId: '',
      startsAt: '',
      endsAt: '',
    })
    expect(errors.map((e) => e.field)).toEqual([
      'title',
      'component_id',
      'starts_at',
      'ends_at',
    ])
  })

  it('reports an end-after-start violation on the End field (shared rule with the server 422)', () => {
    expect(
      validateMaintenanceForm({
        ...VALID,
        startsAt: '2026-07-09T10:00',
        endsAt: '2026-07-09T09:00',
      }),
    ).toEqual([{ field: 'ends_at', message: 'End must be after start.' }])
  })

  it('does not ALSO report an ordering violation when End is simply missing (required wins, no duplicate ends_at error)', () => {
    const errors = validateMaintenanceForm({ ...VALID, endsAt: '' })
    expect(errors.filter((e) => e.field === 'ends_at')).toHaveLength(1)
  })

  it('treats an equal start/end instant as invalid too (strictly greater than, matching the backend rule)', () => {
    expect(
      validateMaintenanceForm({
        ...VALID,
        startsAt: '2026-07-09T09:00',
        endsAt: '2026-07-09T09:00',
      }),
    ).toEqual([{ field: 'ends_at', message: 'End must be after start.' }])
  })
})
