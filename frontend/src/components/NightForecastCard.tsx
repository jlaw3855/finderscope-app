import { memo, useMemo } from 'react'

import type { NightForecast } from '../types/forecast'
import type { MoonEnrichmentEntry } from '../types/moon-enrichment'
import { formatNightColumnDate } from '../lib/astronomy-format'
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
  onSelect: (index: number) => void
  nightIndex: number
  moonEnrichment?: MoonEnrichmentEntry | null
  moonEnrichmentLoading?: boolean
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

function ratingClass(rating: string): string {
  return rating.toLowerCase()
}

function formatBestHourRange(start: string, end: string): string {
  return `${formatHour12(start)}–${formatHour12(end)}`
}

function NightForecastCardComponent({
  night,
  selected,
  onSelect,
  nightIndex,
  moonEnrichment,
  moonEnrichmentLoading = false,
}: NightForecastCardProps) {
  const fallbackMoonLabel =
    MOON_PHASE_LABELS[night.moon_phase] ?? night.moon_phase.replace(/_/g, ' ')
  const displayPhaseName = moonEnrichment?.phase_name ?? fallbackMoonLabel
  const weatherAverages = useMemo(() => averageHourlyWeather(night.hourly), [night.hourly])

  return (
    <button
      type="button"
      className={`night-card ${selected ? 'selected' : ''}`}
      data-testid="night-card"
      onClick={() => onSelect(nightIndex)}
    >
      <div className="night-card-header">
        <span className="night-date">{formatNightColumnDate(night.date)}</span>
        <span className={`rating-badge ${ratingClass(night.rating)}`}>{night.rating}</span>
      </div>

      {night.meteor_showers.length > 0 && (
        <div className="meteor-shower-badges" data-testid="meteor-shower-badges">
          {night.meteor_showers.map((shower) => (
            <span
              key={shower.id}
              className="meteor-shower-badge"
              title={
                shower.zhr_nominal != null
                  ? `${shower.name} peak · nominal ZHR ~${shower.zhr_nominal}`
                  : `${shower.name} peak`
              }
            >
              {shower.name}
            </span>
          ))}
        </div>
      )}

      {night.no_darkness ? (
        <p className="night-detail muted">No astronomical darkness this night.</p>
      ) : (
        <>
          <div className="night-moon-row">
            <div className="night-moon-visual" aria-hidden={!moonEnrichment?.visual_url}>
              {moonEnrichment?.visual_url ? (
                <img
                  src={moonEnrichment.visual_url}
                  alt=""
                  className="night-moon-image"
                  data-testid="moon-visual"
                />
              ) : (
                <div
                  className={`night-moon-placeholder${moonEnrichmentLoading ? ' loading' : ''}`}
                  data-testid="moon-visual-placeholder"
                />
              )}
            </div>
            <div className="night-moon-copy">
              <p className="night-detail night-phase-name">{displayPhaseName}</p>
              <p className="night-detail">
                {Math.round(night.moon_illumination)}% disk lit
                {moonEnrichment?.age_days != null && (
                  <> · {moonEnrichment.age_days.toFixed(1)} day lunar age</>
                )}
              </p>
              {moonEnrichment?.special_labels && moonEnrichment.special_labels.length > 0 && (
                <div className="moon-label-badges">
                  {moonEnrichment.special_labels.map((label) => (
                    <span key={label} className="moon-label-badge">
                      {label}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          <p className="night-score">{night.score ?? '—'}/100</p>
          <p className="night-temps">
            High {formatTemperature(night.temperature_high)} · Low{' '}
            {formatTemperature(night.temperature_low)}
          </p>
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

export const NightForecastCard = memo(NightForecastCardComponent)
