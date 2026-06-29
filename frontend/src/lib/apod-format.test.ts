import { describe, expect, it } from 'vitest'

import { formatApodExplanation } from './apod-format'

describe('formatApodExplanation', () => {
  it('removes the Sky Surprise promotional footer', () => {
    const explanation =
      'Main caption about auroras and sunspots. ' +
      'Sky Surprise: What picture did APOD feature on your birthday? (after 1995)'

    expect(formatApodExplanation(explanation)).toBe(
      'Main caption about auroras and sunspots.',
    )
  })

  it('returns the explanation unchanged when Sky Surprise is absent', () => {
    const explanation = 'A plain APOD caption with no footer.'
    expect(formatApodExplanation(explanation)).toBe(explanation)
  })
})
