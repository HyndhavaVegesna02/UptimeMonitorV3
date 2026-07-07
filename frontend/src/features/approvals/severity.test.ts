import { describe, expect, it } from 'vitest'
import { deriveSeverity } from './severity'

describe('deriveSeverity', () => {
  it('maps major_outage to the "Major" severity on the down tone', () => {
    expect(deriveSeverity('major_outage')).toEqual({ tone: 'down', label: 'Major' })
  })

  it('maps partial_outage to the "Partial" severity on the partial tone', () => {
    expect(deriveSeverity('partial_outage')).toEqual({ tone: 'partial', label: 'Partial' })
  })

  it('maps degraded to the "Degraded" severity on the degraded tone', () => {
    expect(deriveSeverity('degraded')).toEqual({ tone: 'degraded', label: 'Degraded' })
  })

  it('falls back to the "Unknown" severity for any other to_status (e.g. operational)', () => {
    expect(deriveSeverity('operational')).toEqual({ tone: 'unknown', label: 'Unknown' })
  })

  it('falls back to the "Unknown" severity for an unrecognized/garbage value', () => {
    expect(deriveSeverity('some_future_status')).toEqual({ tone: 'unknown', label: 'Unknown' })
  })
})
