import { describe, expect, it } from 'vitest'

import type { CloudCoverBreakdown, HourlyScore, PrecipitationBreakdown } from '../types/forecast'
import {
  averageHourlyWeather,
  createWeatherFormatters,
  formatCloudCover,
  formatHour12,
  formatMoonAltitude,
  formatMoonIlluminationEffective,
  formatMoonSkyGlowAvg,
  formatPrecipitationProbability,
} from './weather-format'

const imperial = createWeatherFormatters('imperial')
const {
  formatTemperature,
  formatVisibility,
  formatPrecipitation: formatPrecipitationMm,
  formatPrecipitationSummary,
  formatCloudLayers,
  formatHourlyTooltip,
} = imperial

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

  it('uses one decimal below 10 mi (imperial default)', () => {
    expect(formatVisibility(5500)).toBe('3.4 mi')
  })

  it('rounds at or above 10 mi (imperial default)', () => {
    expect(formatVisibility(20000)).toBe('12 mi')
  })
})

describe('createWeatherFormatters', () => {
  const imperial = createWeatherFormatters('imperial')
  const metric = createWeatherFormatters('metric')

  describe('temperature', () => {
    it('formats imperial Fahrenheit', () => {
      expect(imperial.formatTemperature(72.4)).toBe('72°F')
    })

    it('formats metric Celsius with rounding', () => {
      expect(metric.formatTemperature(72.4)).toBe('22°C')
    })

    it('uses one decimal for small metric Celsius values', () => {
      expect(metric.formatTemperature(46)).toBe('7.8°C')
    })
  })

  describe('visibility', () => {
    it('formats metric kilometers', () => {
      expect(metric.formatVisibility(5500)).toBe('5.5 km')
      expect(metric.formatVisibility(12500)).toBe('13 km')
    })

    it('formats imperial miles', () => {
      expect(imperial.formatVisibility(5500)).toBe('3.4 mi')
      expect(imperial.formatVisibility(20000)).toBe('12 mi')
    })
  })

  describe('precipitation', () => {
    it('formats metric millimeters', () => {
      expect(metric.formatPrecipitation(0)).toBe('0 mm')
      expect(metric.formatPrecipitation(0.05)).toBe('<0.1 mm')
      expect(metric.formatPrecipitation(0.4)).toBe('0.4 mm')
    })

    it('formats imperial inches', () => {
      expect(imperial.formatPrecipitation(0)).toBe('0 in')
      expect(imperial.formatPrecipitation(0.05)).toBe('<0.01 in')
      expect(imperial.formatPrecipitation(6.35)).toBe('0.3 in')
    })
  })

  describe('temperatureUnitLabel', () => {
    it('returns unit labels for axis titles', () => {
      expect(imperial.temperatureUnitLabel).toBe('°F')
      expect(metric.temperatureUnitLabel).toBe('°C')
    })
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
  it('formats zero (imperial default)', () => {
    expect(formatPrecipitationMm(0)).toBe('0 in')
  })

  it('formats trace amounts (imperial default)', () => {
    expect(formatPrecipitationMm(0.05)).toBe('<0.01 in')
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
  it('joins precipitation summary fields (imperial default)', () => {
    const precip: PrecipitationBreakdown = {
      total_mm: 6.35,
      max_hourly_mm: 2.54,
      max_probability: 25,
    }
    expect(formatPrecipitationSummary(precip)).toBe('0.3 in total · 0.1 in max/hr · 25% chance')
  })
})

describe('formatMoonSkyGlowAvg', () => {
  it('formats average sky glow percentage', () => {
    expect(formatMoonSkyGlowAvg(31.4)).toBe('31%')
  })

  it('returns em dash for null', () => {
    expect(formatMoonSkyGlowAvg(null)).toBe('—')
  })
})

describe('formatMoonIlluminationEffective', () => {
  it('shows Down when below horizon', () => {
    const entry: HourlyScore = {
      time: '22:00',
      at: '2025-06-20T22:00',
      score: 90,
      moon_up: false,
      moon_illumination_effective: 0,
    }
    expect(formatMoonIlluminationEffective(entry)).toBe('Down')
  })

  it('shows effective sky glow percentage when moon is up', () => {
    const entry: HourlyScore = {
      time: '04:00',
      at: '2025-06-21T04:00',
      score: 75,
      moon_up: true,
      moon_illumination_effective: 31,
      moon_altitude: 25.3,
    }
    expect(formatMoonIlluminationEffective(entry)).toBe('31%')
  })
})

describe('formatMoonAltitude', () => {
  it('shows degrees when moon is above horizon', () => {
    const entry: HourlyScore = {
      time: '04:00',
      at: '2025-06-21T04:00',
      score: 75,
      moon_up: true,
      moon_altitude: 25.3,
    }
    expect(formatMoonAltitude(entry)).toBe('25°')
  })

  it('returns em dash when moon is down', () => {
    const entry: HourlyScore = {
      time: '22:00',
      at: '2025-06-20T22:00',
      score: 90,
      moon_up: false,
      moon_altitude: -5,
    }
    expect(formatMoonAltitude(entry)).toBe('—')
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
