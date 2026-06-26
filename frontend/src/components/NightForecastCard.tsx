import type { NightForecast } from '../types/forecast'
import {
  formatCloudCover,
  formatHour12,
  formatTemperature,
  formatVisibility,
  formatMoonSkyGlowAvg,
  averageHourlyWeather,
} from '../lib/weather-format'
import { CloudBreakdown } from './CloudBreakdown'
import { PrecipitationBreakdownView } from './PrecipitationBreakdownView'

interface NightForecastCardProps {
  night: NightForecast
  selected: boolean
  onSelect: () => void
}

const MOON_PHASE_LABELS: Record<string, string> = {
  NEW_MOON: 'New Moon',
  WAXING_CRESCENT: 'Waxing Crescent',
  FIRST_QUARTER: 'First Quarter',
  WAXING_GIBBOUS: 'Waxing Gibbous',
  FULL_MOON: 'Full Moon',
  WANING_GIBBOUS: 'Waning Gibbous',
  LAST_QUARTER: 'Last Quarter',
  WANING_CRESCENT: 'Waning Crescent',
}

function formatDate(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00`)
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

function ratingClass(rating: string): string {
  return rating.toLowerCase()
}

function formatBestHourRange(start: string, end: string): string {
  return `${formatHour12(start)}–${formatHour12(end)}`
}

export function NightForecastCard({ night, selected, onSelect }: NightForecastCardProps) {
  const moonLabel = MOON_PHASE_LABELS[night.moon_phase] ?? night.moon_phase.replace(/_/g, ' ')
  const weatherAverages = averageHourlyWeather(night.hourly)

  return (
    <button
      type="button"
      className={`night-card ${selected ? 'selected' : ''}`}
      data-testid="night-card"
      onClick={onSelect}
    >
      <div className="night-card-header">
        <span className="night-date">{formatDate(night.date)}</span>
        <span className={`rating-badge ${ratingClass(night.rating)}`}>{night.rating}</span>
      </div>

      {night.no_darkness ? (
        <p className="night-detail muted">No astronomical darkness this night.</p>
      ) : (
        <>
          <p className="night-score">{night.score ?? '—'}/100</p>
          <p className="night-temps">
            High {formatTemperature(night.temperature_high)} · Low{' '}
            {formatTemperature(night.temperature_low)}
          </p>
          <p className="night-detail">{moonLabel} · {Math.round(night.moon_illumination)}% disk lit</p>
          {night.moon_sky_glow_avg != null && (
            <p className="night-detail">
              Avg moon sky glow during darkness: {formatMoonSkyGlowAvg(night.moon_sky_glow_avg)}
            </p>
          )}
          {(night.moonrise || night.moonset) && (
            <p className="night-detail">
              {night.moonrise && <>Moonrise {formatHour12(night.moonrise)}</>}
              {night.moonrise && night.moonset && ' · '}
              {night.moonset && <>Moonset {formatHour12(night.moonset)}</>}
            </p>
          )}
          {night.hourly.length > 0 && (
            <p className="night-detail night-weather">
              {formatCloudCover(weatherAverages.avgCloudCover)} avg clouds ·{' '}
              {formatVisibility(weatherAverages.avgVisibility)} avg visibility
            </p>
          )}
          <CloudBreakdown cloud={night.cloud_cover} compact />
          <PrecipitationBreakdownView precipitation={night.precipitation} compact />
          {night.dark_window && (
            <p className="night-detail">
              Dark sky: {formatHour12(night.dark_window.start)} –{' '}
              {formatHour12(night.dark_window.end)}
            </p>
          )}
          {night.best_hours.length > 0 && (
            <p className="night-detail best-hours">
              Best:{' '}
              {night.best_hours
                .map((window) => formatBestHourRange(window.start, window.end))
                .join(', ')}
            </p>
          )}
        </>
      )}
    </button>
  )
}
