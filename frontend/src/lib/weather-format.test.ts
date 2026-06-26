import { describe, expect, it } from 'vitest'

import type { CloudCoverBreakdown, HourlyScore, PrecipitationBreakdown } from '../types/forecast'
import {
  averageHourlyWeather,
  formatCloudCover,
  formatCloudLayers,
  formatHour12,
  formatHourlyTooltip,
  formatPrecipitationMm,
  formatPrecipitationProbability,
  formatPrecipitationSummary,
  formatTemperature,
  formatVisibility,
} from './weather-format'

describe('formatHour12', () => {
  it('formats midnight as 12:00 AM', () => {
    expect(formatHour12('00:00')).toBe('12:00 AM')
  })

  it('formats afternoon times', () => {
    expect(formatHour12('13:30')).toBe('1:30 PM')
  })

  it('returns invalid input unchanged', () => {
    expect(formatHour12('invalid')).toBe('invalid')
  })
})

describe('formatCloudCover', () => {
  it('returns em dash for null', () => {
    expect(formatCloudCover(null)).toBe('—')
  })

  it('rounds percentages', () => {
    expect(formatCloudCover(42.6)).toBe('43%')
  })
})

describe('formatVisibility', () => {
  it('returns em dash for null', () => {
    expect(formatVisibility(undefined)).toBe('—')
  })

  it('uses one decimal below 10 km', () => {
    expect(formatVisibility(5500)).toBe('5.5 km')
  })

  it('rounds at or above 10 km', () => {
    expect(formatVisibility(12500)).toBe('13 km')
  })
})

describe('formatTemperature', () => {
  it('returns em dash for null', () => {
    expect(formatTemperature(null)).toBe('—')
  })

  it('formats Fahrenheit', () => {
    expect(formatTemperature(72.4)).toBe('72°F')
  })
})

describe('formatPrecipitationMm', () => {
  it('formats zero', () => {
    expect(formatPrecipitationMm(0)).toBe('0 mm')
  })

  it('formats trace amounts', () => {
    expect(formatPrecipitationMm(0.05)).toBe('<0.1 mm')
  })

  it('returns em dash for null', () => {
    expect(formatPrecipitationMm(null)).toBe('—')
  })
})

describe('formatPrecipitationProbability', () => {
  it('formats probability', () => {
    expect(formatPrecipitationProbability(33.6)).toBe('34%')
  })
})

describe('averageHourlyWeather', () => {
  it('returns null averages for empty input', () => {
    expect(averageHourlyWeather([])).toEqual({
      avgCloudCover: null,
      avgVisibility: null,
    })
  })

  it('ignores null fields when averaging', () => {
    const hourly: HourlyScore[] = [
      {
        time: '22:00',
        at: '2025-06-20T22:00',
        score: 80,
        cloud_cover: 10,
        visibility: 20000,
      },
      {
        time: '23:00',
        at: '2025-06-20T23:00',
        score: 75,
        cloud_cover: 20,
      },
    ]

    expect(averageHourlyWeather(hourly)).toEqual({
      avgCloudCover: 15,
      avgVisibility: 20000,
    })
  })
})

describe('formatCloudLayers', () => {
  it('joins low, mid, and high layers', () => {
    const cloud: CloudCoverBreakdown = { total: 30, low: 10, mid: 15, high: 5 }
    expect(formatCloudLayers(cloud)).toBe('L 10% · M 15% · H 5%')
  })
})

describe('formatPrecipitationSummary', () => {
  it('joins precipitation summary fields', () => {
    const precip: PrecipitationBreakdown = {
      total_mm: 0.4,
      max_hourly_mm: 0.2,
      max_probability: 25,
    }
    expect(formatPrecipitationSummary(precip)).toBe('0.4 mm total · 0.2 mm max/hr · 25% chance')
  })
})

describe('formatHourlyTooltip', () => {
  it('builds a multi-line tooltip', () => {
    const entry: HourlyScore = {
      time: '22:00',
      at: '2025-06-20T22:00',
      score: 88,
      cloud_cover: 10,
      cloud_cover_low: 2,
      cloud_cover_mid: 3,
      cloud_cover_high: 5,
      visibility: 20000,
      precipitation: 0,
      precipitation_probability: 0,
      dew_point: 8,
      temperature: 18,
    }

    const tooltip = formatHourlyTooltip('10:00 PM', entry)
    expect(tooltip).toContain('10:00 PM: 88/100')
    expect(tooltip).toContain('Clouds: 10%')
    expect(tooltip).toContain('Dew point: 8°F')
  })
})
