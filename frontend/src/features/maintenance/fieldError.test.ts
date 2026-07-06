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
})
