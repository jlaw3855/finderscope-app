import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import type { HourlyScore } from '../types/forecast'
import { DewPointChart } from './DewPointChart'
import { withUnitProvider } from '../test/with-unit-provider'

const sampleHourly: HourlyScore[] = [
  {
    time: '22:00',
    at: '2025-06-20T22:00:00',
    score: 98,
    dew_point: 42,
    temperature: 52,
  },
  {
    time: '23:00',
    at: '2025-06-20T23:00:00',
    score: 97,
    dew_point: 43,
    temperature: 51,
  },
  {
    time: '00:00',
    at: '2025-06-21T00:00:00',
    score: 96,
    dew_point: 44,
    temperature: 50,
  },
]

describe('DewPointChart', () => {
  it('renders dew and air temperature polylines', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(<DewPointChart hourly={sampleHourly} stepMinutes={60} />),
    )
    expect(html).toContain('hourly-temp-line--dew')
    expect(html).toContain('hourly-temp-line--air')
    expect(html).toContain('hourly-temp-dot--dew')
    expect(html).toContain('hourly-temp-dot--air')
  })

  it('renders dew-only when temperature is missing', () => {
    const dewOnly = sampleHourly.map(({ temperature: _temp, ...entry }) => entry)
    const html = renderToStaticMarkup(withUnitProvider(<DewPointChart hourly={dewOnly} stepMinutes={60} />))
    expect(html).toContain('hourly-temp-line--dew')
    expect(html).not.toContain('hourly-temp-line--air')
  })

  it('returns null without dew point data', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(
        <DewPointChart hourly={[{ time: '22:00', at: '2025-06-20T22:00:00', score: 90 }]} />,
      ),
    )
    expect(html).toBe('')
  })

  it('sizes svg to aligned grid width', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(<DewPointChart hourly={sampleHourly} stepMinutes={60} />),
    )
    expect(html).toContain('width="321"')
  })
})
