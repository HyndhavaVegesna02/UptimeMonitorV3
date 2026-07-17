import { describe, expect, it } from 'vitest'
import { actionCardView } from './actionCard'

describe('actionCardView', () => {
  it('renders an honest em-dash in the neutral tone for an unresolved (loading/error) count — never a fabricated 0', () => {
    expect(actionCardView(undefined)).toEqual({ value: '—', tone: 'neutral' })
  })

  it('renders a real 0 in the neutral tone — nothing pending is good news, not an alert (journal D4)', () => {
    expect(actionCardView(0)).toEqual({ value: 0, tone: 'neutral' })
  })

  it('renders any count above 0 in the accent (indigo/info, never alert-red) tone', () => {
    expect(actionCardView(1)).toEqual({ value: 1, tone: 'accent' })
    expect(actionCardView(5)).toEqual({ value: 5, tone: 'accent' })
  })
})
