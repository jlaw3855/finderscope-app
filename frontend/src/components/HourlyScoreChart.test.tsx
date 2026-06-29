import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import type { HourlyScore } from '../types/forecast'
import { HourlyScoreChart } from './HourlyScoreChart'
import { withUnitProvider } from '../test/with-unit-provider'

const sampleHourly: HourlyScore[] = [
  {
    time: '22:00',
    at: '2025-06-20T22:00:00',
    score: 90,
    visibility: 12000,
    seeing: 2,
    transparency: 3,
  },
  {
    time: '23:00',
    at: '2025-06-20T23:00:00',
    score: 88,
    visibility: 11000,
    seeing: 2,
    transparency: 3,
  },
]

describe('HourlyScoreChart', () => {
  it('always renders the visibility metric row', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(
        <HourlyScoreChart hourly={sampleHourly} date="2025-06-20" astroForecastLimited />,
      ),
    )
    expect(html).toContain('Visibility')
  })

  it('renders seeing and transparency when astro data is available', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(
        <HourlyScoreChart
          hourly={sampleHourly}
          date="2025-06-20"
          astroForecastLimited={false}
        />,
      ),
    )
    expect(html).toContain('Seeing')
    expect(html).toContain('Transparency')
    expect(html).toContain('Visibility')
  })

  it('omits seeing and transparency rows when astro forecast is limited', () => {
    const limitedHourly: HourlyScore[] = sampleHourly.map(
      ({ seeing: _seeing, transparency: _transparency, ...entry }) => entry,
    )
    const html = renderToStaticMarkup(
      withUnitProvider(
        <HourlyScoreChart
          hourly={limitedHourly}
          date="2025-06-20"
          astroForecastLimited
        />,
      ),
    )
    expect(html).not.toContain('hourly-metric-label" title="Astronomical seeing')
    expect(html).not.toContain('hourly-metric-label" title="Atmospheric transparency')
  })
})
