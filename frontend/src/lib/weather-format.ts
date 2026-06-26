import type { CloudCoverBreakdown, HourlyScore, PrecipitationBreakdown } from '../types/forecast'

export function formatHour12(time24: string): string {
  const [hourPart, minutePart] = time24.split(':')
  const hour = Number(hourPart)
  const minute = Number(minutePart)
  if (Number.isNaN(hour) || Number.isNaN(minute)) {
    return time24
  }

  const period = hour >= 12 ? 'PM' : 'AM'
  const hour12 = hour % 12 || 12
  return `${hour12}:${String(minute).padStart(2, '0')} ${period}`
}

export function formatCloudCover(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}%`
}

export function formatVisibility(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  const km = value / 1000
  if (km >= 10) {
    return `${Math.round(km)} km`
  }
  return `${km.toFixed(1)} km`
}

export function formatTemperature(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}°F`
}

export function formatPrecipitationMm(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  if (value === 0) {
    return '0 mm'
  }
  if (value < 0.1) {
    return '<0.1 mm'
  }
  return `${value.toFixed(1)} mm`
}

export function formatPrecipitationProbability(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}%`
}

export interface HourlyWeatherAverages {
  avgCloudCover: number | null
  avgVisibility: number | null
}

export function averageHourlyWeather(hourly: HourlyScore[]): HourlyWeatherAverages {
  const cloudValues = hourly
    .map((entry) => entry.cloud_cover)
    .filter((value): value is number => value != null)
  const visibilityValues = hourly
    .map((entry) => entry.visibility)
    .filter((value): value is number => value != null)

  return {
    avgCloudCover:
      cloudValues.length > 0
        ? cloudValues.reduce((sum, value) => sum + value, 0) / cloudValues.length
        : null,
    avgVisibility:
      visibilityValues.length > 0
        ? visibilityValues.reduce((sum, value) => sum + value, 0) / visibilityValues.length
        : null,
  }
}

export function formatCloudLayers(cloud: CloudCoverBreakdown): string {
  return `L ${formatCloudCover(cloud.low)} · M ${formatCloudCover(cloud.mid)} · H ${formatCloudCover(cloud.high)}`
}

export function formatPrecipitationSummary(precip: PrecipitationBreakdown): string {
  return [
    `${formatPrecipitationMm(precip.total_mm)} total`,
    `${formatPrecipitationMm(precip.max_hourly_mm)} max/hr`,
    `${formatPrecipitationProbability(precip.max_probability)} chance`,
  ].join(' · ')
}

export function formatMoonSkyGlowAvg(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}%`
}

export function formatMoonIlluminationEffective(entry: HourlyScore): string {
  if (entry.moon_up === false) {
    return 'Moon down'
  }
  if (entry.moon_illumination_effective == null) {
    return '—'
  }
  return `${Math.round(entry.moon_illumination_effective)}%`
}

export function formatMoonAltitude(entry: HourlyScore): string {
  if (entry.moon_up === false || entry.moon_altitude == null || entry.moon_altitude <= 0) {
    return '—'
  }
  return `${Math.round(entry.moon_altitude)}°`
}

export function formatHourlyTooltip(label: string, entry: HourlyScore): string {
  return [
    `${label}: ${entry.score}/100`,
    `Moon sky glow: ${formatMoonIlluminationEffective(entry)}`,
    `Moon altitude: ${formatMoonAltitude(entry)}`,
    `Clouds: ${formatCloudCover(entry.cloud_cover)} (L ${formatCloudCover(entry.cloud_cover_low)} / M ${formatCloudCover(entry.cloud_cover_mid)} / H ${formatCloudCover(entry.cloud_cover_high)})`,
    `Visibility: ${formatVisibility(entry.visibility)}`,
    `Precip: ${formatPrecipitationMm(entry.precipitation)} (${formatPrecipitationProbability(entry.precipitation_probability)} chance)`,
    `Dew point: ${formatTemperature(entry.dew_point)} · Temp: ${formatTemperature(entry.temperature)}`,
  ].join('\n')
}
