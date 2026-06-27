import { describe, expect, it } from 'vitest'

import { darkWindowMidpointIso } from './moon-sample-time'

describe('darkWindowMidpointIso', () => {
  it('returns midpoint for darkness spanning midnight', () => {
    expect(
      darkWindowMidpointIso('2025-06-20', { start: '21:30', end: '04:45' }),
    ).toBe('2025-06-21T01:08:00')
  })

  it('returns midpoint for same-day darkness', () => {
    expect(
      darkWindowMidpointIso('2025-06-20', { start: '20:00', end: '23:00' }),
    ).toBe('2025-06-20T21:30:00')
  })
})
