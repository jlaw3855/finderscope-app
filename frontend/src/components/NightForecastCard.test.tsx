import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import type { NightForecast } from '../types/forecast'
import { NightForecastCard } from './NightForecastCard'
import { withUnitProvider } from '../test/with-unit-provider'

const baseNight: NightForecast = {
  date: '2025-06-20',
  rating: 'Good',
  score: 75,
  moon_phase: 'WANING_GIBBOUS',
  moon_illumination: 72,
  cloud_cover: { total: 10, low: 2, mid: 3, high: 5 },
  precipitation: { total_mm: 0, max_hourly_mm: 0, max_probability: 5 },
  best_hours: [],
  hourly: [
    {
      time: '22:00',
      at: '2025-06-20T22:00:00',
      score: 80,
      visibility: 15000,
      cloud_cover: 10,
      seeing: 2,
      transparency: 3,
    },
  ],
  no_darkness: false,
  meteor_showers: [],
  astro_forecast_limited: false,
}

describe('NightForecastCard', () => {
  it('always shows visibility in the weather summary', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(
        <NightForecastCard night={baseNight} selected={false} onSelect={() => {}} nightIndex={0} />,
      ),
    )
    expect(html).toContain('avg visibility')
  })

  it('shows seeing and transparency when astro forecast is available', () => {
    const html = renderToStaticMarkup(
      withUnitProvider(
        <NightForecastCard night={baseNight} selected={false} onSelect={() => {}} nightIndex={0} />,
      ),
    )
    expect(html).toContain('avg seeing')
    expect(html).toContain('avg transparency')
  })

  it('hides seeing and transparency when astro forecast is limited', () => {
    const limitedNight = { ...baseNight, astro_forecast_limited: true }
    const html = renderToStaticMarkup(
      withUnitProvider(
        <NightForecastCard
          night={limitedNight}
          selected={false}
          onSelect={() => {}}
          nightIndex={0}
        />,
      ),
    )
    expect(html).toContain('avg visibility')
    expect(html).not.toContain('avg seeing')
    expect(html).not.toContain('avg transparency')
  })
})
