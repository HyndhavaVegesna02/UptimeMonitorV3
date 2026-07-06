import { describe, expect, it } from 'vitest'
import { fieldErrorFromDetail } from './fieldError'

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
