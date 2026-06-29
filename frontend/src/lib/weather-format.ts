import type { CloudCoverBreakdown, HourlyScore, PrecipitationBreakdown } from '../types/forecast'
import {
  fahrenheitToCelsius,
  formatDecimal,
  metersToKm,
  metersToMiles,
  mmToInches,
  type UnitSystem,
} from './unit-system'

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

const SEEING_LABELS: Record<number, string> = {
  1: '<0.5″',
  2: '0.5–0.75″',
  3: '0.75–1″',
  4: '1–1.25″',
  5: '1.25–1.5″',
  6: '1.5–2″',
  7: '2–2.5″',
  8: '>2.5″',
}

const TRANSPARENCY_LABELS: Record<number, string> = {
  1: '<0.3 mag/am',
  2: '0.3–0.4',
  3: '0.4–0.5',
  4: '0.5–0.6',
  5: '0.6–0.7',
  6: '0.7–0.85',
  7: '0.85–1',
  8: '>1 mag/am',
}

export function formatSeeing(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return SEEING_LABELS[value] ?? String(value)
}

export function formatTransparency(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return TRANSPARENCY_LABELS[value] ?? String(value)
}

export function formatPrecipitationProbability(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}%`
}

function formatDistanceFromMeters(value: number, units: UnitSystem): string {
  if (units === 'metric') {
    const km = metersToKm(value)
    if (km >= 10) {
      return `${Math.round(km)} km`
    }
    return `${formatDecimal(km, 1)} km`
  }

  const miles = metersToMiles(value)
  if (miles >= 10) {
    return `${Math.round(miles)} mi`
  }
  return `${formatDecimal(miles, 1)} mi`
}

function formatTemperatureFahrenheit(value: number, units: UnitSystem): string {
  if (units === 'imperial') {
    return `${Math.round(value)}°F`
  }

  const celsius = fahrenheitToCelsius(value)
  if (Math.abs(celsius) < 10) {
    return `${formatDecimal(celsius, 1)}°C`
  }
  return `${Math.round(celsius)}°C`
}

function formatPrecipitationFromMm(value: number, units: UnitSystem): string {
  if (units === 'metric') {
    if (value === 0) {
      return '0 mm'
    }
    if (value < 0.1) {
      return '<0.1 mm'
    }
    return `${formatDecimal(value, 1)} mm`
  }

  if (value === 0) {
    return '0 in'
  }

  const inches = mmToInches(value)
  if (inches < 0.01) {
    return '<0.01 in'
  }
  if (inches < 0.1) {
    return `${formatDecimal(inches, 2)} in`
  }
  return `${formatDecimal(inches, 1)} in`
}

export interface WeatherFormatters {
  unitSystem: UnitSystem
  temperatureUnitLabel: string
  formatTemperature: (value: number | null | undefined) => string
  formatVisibility: (value: number | null | undefined) => string
  formatPrecipitation: (value: number | null | undefined) => string
  formatCloudLayers: (cloud: CloudCoverBreakdown) => string
  formatPrecipitationSummary: (precip: PrecipitationBreakdown) => string
  formatHourlyTooltip: (label: string, entry: HourlyScore) => string
}

export function createWeatherFormatters(units: UnitSystem): WeatherFormatters {
  const formatTemperature = (value: number | null | undefined): string => {
    if (value == null) {
      return '—'
    }
    return formatTemperatureFahrenheit(value, units)
  }

  const formatVisibility = (value: number | null | undefined): string => {
    if (value == null) {
      return '—'
    }
    return formatDistanceFromMeters(value, units)
  }

  const formatPrecipitation = (value: number | null | undefined): string => {
    if (value == null) {
      return '—'
    }
    return formatPrecipitationFromMm(value, units)
  }

  const formatCloudLayers = (cloud: CloudCoverBreakdown): string => {
    return `L ${formatCloudCover(cloud.low)} · M ${formatCloudCover(cloud.mid)} · H ${formatCloudCover(cloud.high)}`
  }

  const formatPrecipitationSummary = (precip: PrecipitationBreakdown): string => {
    return [
      `${formatPrecipitation(precip.total_mm)} total`,
      `${formatPrecipitation(precip.max_hourly_mm)} max/hr`,
      `${formatPrecipitationProbability(precip.max_probability)} chance`,
    ].join(' · ')
  }

  const formatHourlyTooltip = (label: string, entry: HourlyScore): string => {
    const lines = [
      `${label}: ${entry.score}/100`,
      `Moon sky glow: ${formatMoonIlluminationEffective(entry)}`,
      `Moon altitude: ${formatMoonAltitude(entry)}`,
      `Clouds: ${formatCloudCover(entry.cloud_cover)} (L ${formatCloudCover(entry.cloud_cover_low)} / M ${formatCloudCover(entry.cloud_cover_mid)} / H ${formatCloudCover(entry.cloud_cover_high)})`,
    ]

    if (entry.seeing != null || entry.transparency != null) {
      lines.push(`Seeing: ${formatSeeing(entry.seeing)}`)
      lines.push(`Transparency: ${formatTransparency(entry.transparency)}`)
    }
    lines.push(`Visibility: ${formatVisibility(entry.visibility)}`)

    lines.push(
      `Precip: ${formatPrecipitation(entry.precipitation)} (${formatPrecipitationProbability(entry.precipitation_probability)} chance)`,
      `Dew point: ${formatTemperature(entry.dew_point)} · Temp: ${formatTemperature(entry.temperature)}`,
    )

    return lines.join('\n')
  }

  return {
    unitSystem: units,
    temperatureUnitLabel: units === 'metric' ? '°C' : '°F',
    formatTemperature,
    formatVisibility,
    formatPrecipitation,
    formatCloudLayers,
    formatPrecipitationSummary,
    formatHourlyTooltip,
  }
}

/** Imperial defaults — backward-compatible helpers for tests and non-React code. */
const imperialFormatters = createWeatherFormatters('imperial')

export const formatTemperature = imperialFormatters.formatTemperature
export const formatVisibility = imperialFormatters.formatVisibility
export const formatPrecipitationMm = imperialFormatters.formatPrecipitation
export const formatPrecipitationSummary = imperialFormatters.formatPrecipitationSummary
export const formatCloudLayers = imperialFormatters.formatCloudLayers
export const formatHourlyTooltip = imperialFormatters.formatHourlyTooltip
