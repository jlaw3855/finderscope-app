import type { HourlyScore } from '../types/forecast'
import {
  formatCloudCover,
  formatHour12,
  formatHourlyTooltip,
  formatPrecipitationMm,
  formatPrecipitationProbability,
  formatTemperature,
  formatVisibility,
  averageHourlyWeather,
} from '../lib/weather-format'
import { CloudBreakdown } from './CloudBreakdown'
import { DewPointChart } from './DewPointChart'
import { PrecipitationBreakdownView } from './PrecipitationBreakdownView'

interface HourlyScoreChartProps {
  hourly: HourlyScore[]
  date: string
}

function formatDate(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00`)
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

function averageCloudBreakdown(hourly: HourlyScore[]) {
  const average = (values: Array<number | null | undefined>) => {
    const filtered = values.filter((value): value is number => value != null)
    if (filtered.length === 0) {
      return null
    }
    return filtered.reduce((sum, value) => sum + value, 0) / filtered.length
  }

  return {
    total: average(hourly.map((entry) => entry.cloud_cover)),
    low: average(hourly.map((entry) => entry.cloud_cover_low)),
    mid: average(hourly.map((entry) => entry.cloud_cover_mid)),
    high: average(hourly.map((entry) => entry.cloud_cover_high)),
  }
}

function summarizePrecipitation(hourly: HourlyScore[]) {
  const amounts = hourly
    .map((entry) => entry.precipitation)
    .filter((value): value is number => value != null)
  const probabilities = hourly
    .map((entry) => entry.precipitation_probability)
    .filter((value): value is number => value != null)

  return {
    total_mm: amounts.length > 0 ? amounts.reduce((sum, value) => sum + value, 0) : null,
    max_hourly_mm: amounts.length > 0 ? Math.max(...amounts) : null,
    max_probability: probabilities.length > 0 ? Math.max(...probabilities) : null,
  }
}

export function HourlyScoreChart({ hourly, date }: HourlyScoreChartProps) {
  const heading = `Hourly scores during darkness — ${formatDate(date)}`
  const averages = averageHourlyWeather(hourly)
  const cloudSummary = averageCloudBreakdown(hourly)
  const precipSummary = summarizePrecipitation(hourly)

  if (hourly.length === 0) {
    return (
      <section className="panel">
        <h2>{heading}</h2>
        <p className="muted">No hourly data during darkness for this night.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <h2>{heading}</h2>
      <p className="hourly-summary muted">
        Avg during darkness: {formatCloudCover(averages.avgCloudCover)} clouds ·{' '}
        {formatVisibility(averages.avgVisibility)} visibility
      </p>

      <div className="hourly-detail-grid">
        <CloudBreakdown cloud={cloudSummary} />
        <PrecipitationBreakdownView precipitation={precipSummary} />
      </div>

      <DewPointChart hourly={hourly} />

      <div className="hourly-chart">
        {hourly.map((entry) => {
          const label = formatHour12(entry.time)
          return (
            <div key={entry.at} className="hourly-bar-group">
              <div className="hourly-bar-track">
                <div
                  className="hourly-bar-fill"
                  style={{ height: `${entry.score}%` }}
                  title={formatHourlyTooltip(label, entry)}
                />
              </div>
              <span className="hourly-label">{label}</span>
              <span className="hourly-weather-label">T {formatCloudCover(entry.cloud_cover)}</span>
              <span className="hourly-weather-label">
                L {formatCloudCover(entry.cloud_cover_low)}
              </span>
              <span className="hourly-weather-label">
                M {formatCloudCover(entry.cloud_cover_mid)}
              </span>
              <span className="hourly-weather-label">
                H {formatCloudCover(entry.cloud_cover_high)}
              </span>
              <span className="hourly-weather-label">
                {formatPrecipitationMm(entry.precipitation)}
              </span>
              <span className="hourly-weather-label">
                {formatPrecipitationProbability(entry.precipitation_probability)}
              </span>
              <span className="hourly-weather-label">
                Dew {formatTemperature(entry.dew_point)}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
