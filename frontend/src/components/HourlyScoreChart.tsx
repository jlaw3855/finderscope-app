import { Fragment } from 'react'

import type { HourlyScore } from '../types/forecast'
import {
  formatCloudCover,
  formatHour12,
  formatHourlyTooltip,
  formatPrecipitationMm,
  formatPrecipitationProbability,
  formatMoonAltitude,
  formatMoonIlluminationEffective,
  formatVisibility,
  averageHourlyWeather,
} from '../lib/weather-format'
import { CloudBreakdown } from './CloudBreakdown'
import { DewPointChart, DewPointChartAxis } from './DewPointChart'
import { shouldShowTimeLabel } from './hourly-chart-layout'
import { PrecipitationBreakdownView } from './PrecipitationBreakdownView'

interface HourlyScoreChartProps {
  hourly: HourlyScore[]
  date: string
  stepMinutes?: number
}

interface HourlyMetricRow {
  id: string
  label: string
  title: string
  group: string
  format: (entry: HourlyScore) => string
}

type HourlyChartRow =
  | { kind: 'group'; id: string; label: string }
  | { kind: 'metric'; row: HourlyMetricRow }

const HOURLY_METRIC_ROWS: HourlyMetricRow[] = [
  {
    id: 'cloud-total',
    label: 'Total clouds',
    title: 'Total cloud cover',
    group: 'Clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover),
  },
  {
    id: 'cloud-low',
    label: 'Low clouds',
    title: 'Low-altitude clouds',
    group: 'Clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_low),
  },
  {
    id: 'cloud-mid',
    label: 'Mid clouds',
    title: 'Mid-altitude clouds',
    group: 'Clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_mid),
  },
  {
    id: 'cloud-high',
    label: 'High clouds',
    title: 'High-altitude clouds',
    group: 'Clouds',
    format: (entry) => formatCloudCover(entry.cloud_cover_high),
  },
  {
    id: 'precip-amount',
    label: 'Precip amount',
    title: 'Precipitation amount',
    group: 'Precipitation',
    format: (entry) => formatPrecipitationMm(entry.precipitation),
  },
  {
    id: 'precip-chance',
    label: 'Precip chance',
    title: 'Chance of precipitation',
    group: 'Precipitation',
    format: (entry) => formatPrecipitationProbability(entry.precipitation_probability),
  },
  {
    id: 'moon-light',
    label: 'Moon glow',
    title: 'Effective moon sky glow',
    group: 'Moon',
    format: (entry) => formatMoonIlluminationEffective(entry),
  },
  {
    id: 'moon-altitude',
    label: 'Moon altitude',
    title: 'Moon altitude',
    group: 'Moon',
    format: (entry) => formatMoonAltitude(entry),
  },
]

function buildHourlyChartRows(): HourlyChartRow[] {
  const rows: HourlyChartRow[] = []
  let lastGroup: string | null = null

  for (const row of HOURLY_METRIC_ROWS) {
    if (row.group !== lastGroup) {
      rows.push({ kind: 'group', id: `group-${row.group}`, label: row.group })
      lastGroup = row.group
    }
    rows.push({ kind: 'metric', row })
  }

  return rows
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

function hasDewPointData(hourly: HourlyScore[]): boolean {
  return hourly.some((entry) => entry.dew_point != null)
}

function HourlyTimeRow({
  hourly,
  stepMinutes,
}: {
  hourly: HourlyScore[]
  stepMinutes: number
}) {
  return (
    <div className="hourly-time-row">
      {hourly.map((entry, index) => {
        const label = formatHour12(entry.time)
        const showLabel = shouldShowTimeLabel(index, hourly.length, stepMinutes)
        return (
          <div key={`time-${entry.at}`} className="hourly-column">
            <span className="hourly-time-label">{showLabel ? label : ''}</span>
          </div>
        )
      })}
    </div>
  )
}

export function HourlyScoreChart({
  hourly,
  date,
  stepMinutes = 60,
}: HourlyScoreChartProps) {
  const heading =
    stepMinutes === 30
      ? `Half-hourly scores during darkness — ${formatDate(date)}`
      : `Hourly scores during darkness — ${formatDate(date)}`
  const averages = averageHourlyWeather(hourly)
  const cloudSummary = averageCloudBreakdown(hourly)
  const precipSummary = summarizePrecipitation(hourly)
  const showTempChart = hasDewPointData(hourly)
  const chartRows = buildHourlyChartRows()

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

      <div
        className={`hourly-chart-layout${stepMinutes === 30 ? ' hourly-chart-layout--half-hour' : ''}${showTempChart ? ' hourly-chart-layout--with-temp' : ''}`}
      >
        {showTempChart && (
          <>
            <div className="hourly-grid-label hourly-grid-row--temp-header">
              <span className="hourly-section-label">Dew point &amp; temp</span>
              <div className="hourly-temp-legend hourly-temp-legend--header">
                <span className="hourly-temp-legend-item">
                  <span className="hourly-temp-legend-swatch hourly-temp-legend-swatch--dew" />
                  Dew point
                </span>
                <span className="hourly-temp-legend-item">
                  <span className="hourly-temp-legend-swatch hourly-temp-legend-swatch--air" />
                  Air temp
                </span>
              </div>
            </div>
            <div
              className="hourly-grid-data hourly-grid-row--temp-header"
              aria-hidden="true"
            />
          </>
        )}

        {showTempChart && (
          <>
            <div className="hourly-grid-label hourly-grid-row--temp-plot" aria-hidden="true">
              <DewPointChartAxis hourly={hourly} />
            </div>
            <div className="hourly-grid-data hourly-grid-row--temp-plot">
              <DewPointChart hourly={hourly} stepMinutes={stepMinutes} />
            </div>
          </>
        )}

        <div className="hourly-grid-label hourly-grid-row--time">
          <span className="hourly-section-label">Time</span>
        </div>
        <div className="hourly-grid-data hourly-grid-row--time">
          <HourlyTimeRow hourly={hourly} stepMinutes={stepMinutes} />
        </div>

        <div className="hourly-grid-label hourly-grid-row--score">
          <span className="hourly-section-label hourly-section-label--score">Score (0–100)</span>
        </div>
        <div className="hourly-grid-data hourly-grid-row--score">
          <div className="hourly-bars-row">
            {hourly.map((entry) => {
              const label = formatHour12(entry.time)
              return (
                <div key={entry.at} className="hourly-column">
                  <div className="hourly-bar-track" title={formatHourlyTooltip(label, entry)}>
                    <div className="hourly-bar-gridline hourly-bar-gridline--100" />
                    <div className="hourly-bar-gridline hourly-bar-gridline--50" />
                    <div className="hourly-bar-gridline hourly-bar-gridline--0" />
                    <span className="hourly-score-value">{entry.score}</span>
                    <div className="hourly-bar-fill" style={{ height: `${entry.score}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {chartRows.map((chartRow) => {
          if (chartRow.kind === 'group') {
            return (
              <Fragment key={chartRow.id}>
                <div className="hourly-grid-label hourly-grid-row--metric-group">
                  <span className="hourly-metric-group-label">{chartRow.label}</span>
                </div>
                <div
                  className="hourly-grid-data hourly-grid-row--metric-group"
                  aria-hidden="true"
                />
              </Fragment>
            )
          }

          const row = chartRow.row
          return (
            <Fragment key={row.id}>
              <div className="hourly-grid-label hourly-grid-row--metric">
                <span className="hourly-metric-label" title={row.title}>
                  {row.label}
                </span>
              </div>
              <div className="hourly-grid-data hourly-grid-row--metric">
                <div className="hourly-metrics-row">
                  {hourly.map((entry) => (
                    <div key={`${row.id}-${entry.at}`} className="hourly-column">
                      <span className="hourly-metric-value" title={row.title}>
                        {row.format(entry)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Fragment>
          )
        })}
      </div>
    </section>
  )
}
