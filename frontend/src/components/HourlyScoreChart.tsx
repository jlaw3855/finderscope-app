import type { HourlyScore } from '../types/forecast'
import {
  formatCloudCover,
  formatHour12,
  formatHourlyTooltip,
  formatPrecipitationMm,
  formatPrecipitationProbability,
  formatTemperature,
  formatVisibility,
  formatMoonAltitude,
  formatMoonIlluminationEffective,
  averageHourlyWeather,
} from '../lib/weather-format'
import { CloudBreakdown } from './CloudBreakdown'
import { DewPointChart } from './DewPointChart'
import { PrecipitationBreakdownView } from './PrecipitationBreakdownView'

interface HourlyScoreChartProps {
  hourly: HourlyScore[]
  date: string
}

interface HourlyMetricRow {
  id: string
  label: string
  format: (entry: HourlyScore) => string
}

const HOURLY_METRIC_ROWS: HourlyMetricRow[] = [
  {
    id: 'cloud-total',
    label: 'Total cloud cover',
    format: (entry) => formatCloudCover(entry.cloud_cover),
  },
  {
    id: 'cloud-low',
    label: 'Low-altitude clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_low),
  },
  {
    id: 'cloud-mid',
    label: 'Mid-altitude clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_mid),
  },
  {
    id: 'cloud-high',
    label: 'High-altitude clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_high),
  },
  {
    id: 'precip-amount',
    label: 'Precipitation amount',
    format: (entry) => formatPrecipitationMm(entry.precipitation),
  },
  {
    id: 'precip-chance',
    label: 'Chance of precipitation',
    format: (entry) => formatPrecipitationProbability(entry.precipitation_probability),
  },
  {
    id: 'moon-light',
    label: 'Effective moon sky glow',
    format: (entry) => formatMoonIlluminationEffective(entry),
  },
  {
    id: 'moon-altitude',
    label: 'Moon altitude',
    format: (entry) => formatMoonAltitude(entry),
  },
  {
    id: 'dew-point',
    label: 'Dew point',
    format: (entry) => formatTemperature(entry.dew_point),
  },
]

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

      <div className="hourly-chart-layout">
        <div className="hourly-metric-labels" aria-hidden="true">
          <div className="hourly-metric-labels-spacer" />
          {HOURLY_METRIC_ROWS.map((row) => (
            <span key={row.id} className="hourly-metric-label">
              {row.label}
            </span>
          ))}
        </div>

        <div className="hourly-chart-scroll">
          <div className="hourly-bars-row">
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
                </div>
              )
            })}
          </div>

          <div className="hourly-metrics-row">
            {hourly.map((entry) => (
              <div key={entry.at} className="hourly-metric-column">
                {HOURLY_METRIC_ROWS.map((row) => (
                  <span key={row.id} className="hourly-metric-value">
                    {row.format(entry)}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
