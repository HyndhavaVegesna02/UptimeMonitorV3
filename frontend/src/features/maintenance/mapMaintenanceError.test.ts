import { describe, expect, it } from 'vitest'
import { mapMaintenanceError } from './mapMaintenanceError'

describe('mapMaintenanceError', () => {
  // THE crux test (plan §Maintenance edge behavior): the end-before-start
  // detail also names "starts_at", so the "strictly greater than" check
  // MUST run first, or this would wrongly map to starts_at instead.
  it('CRUX: "strictly greater than" (end-before-start) maps to ends_at FIRST, even though the message also names starts_at', () => {
    expect(
      mapMaintenanceError('ends_at must be strictly greater than starts_at.'),
    ).toEqual({
      field: 'ends_at',
      message: 'ends_at must be strictly greater than starts_at.',
    })
  })

  it('maps a component_id detail to the component_id field', () => {
    expect(mapMaintenanceError('component_id must be a non-empty string.')).toEqual({
      field: 'component_id',
      message: 'component_id must be a non-empty string.',
    })
  })

  it('maps a starts_at detail (timezone-aware) to the starts_at field', () => {
    expect(mapMaintenanceError('starts_at must be timezone-aware.')).toEqual({
      field: 'starts_at',
      message: 'starts_at must be timezone-aware.',
    })
  })

  it('maps a starts_at detail (must be in UTC) to the starts_at field', () => {
    expect(mapMaintenanceError('starts_at must be in UTC.')).toEqual({
      field: 'starts_at',
      message: 'starts_at must be in UTC.',
    })
  })

  it('maps an ends_at detail (timezone-aware) to the ends_at field', () => {
    expect(mapMaintenanceError('ends_at must be timezone-aware.')).toEqual({
      field: 'ends_at',
      message: 'ends_at must be timezone-aware.',
    })
  })

  it('maps an ends_at detail (must be in UTC) to the ends_at field', () => {
    expect(mapMaintenanceError('ends_at must be in UTC.')).toEqual({
      field: 'ends_at',
      message: 'ends_at must be in UTC.',
    })
  })

  it('falls back to a form-level banner (field: null) when the detail names none of the fields', () => {
    expect(mapMaintenanceError('Internal server error')).toEqual({
      field: null,
      message: 'Internal server error',
    })
  })

  it('falls back to a form-level banner with a generic message when there is no detail at all', () => {
    expect(mapMaintenanceError(undefined)).toEqual({
      field: null,
      message: 'Something went wrong scheduling this window.',
    })
  })
})
