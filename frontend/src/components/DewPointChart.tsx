import type { HourlyScore } from '../types/forecast'
import { formatHour12, formatTemperature } from '../lib/weather-format'
import {
  buildTemperatureScale,
  buildTemperatureTicks,
  getHourlyColumnCenterX,
  getHourlyGridWidth,
  valueToChartY,
} from './hourly-chart-layout'

interface DewPointChartProps {
  hourly: HourlyScore[]
  stepMinutes?: number
}

const CHART_HEIGHT = 220
const PLOT_TOP = 12
const PLOT_BOTTOM = 28

export function DewPointChart({ hourly, stepMinutes = 60 }: DewPointChartProps) {
  const dewPoints = hourly
    .map((entry) => entry.dew_point)
    .filter((value): value is number => value != null)

  if (dewPoints.length === 0) {
    return null
  }

  const temperatures = hourly
    .map((entry) => entry.temperature)
    .filter((value): value is number => value != null)

  const scale = buildTemperatureScale(dewPoints, temperatures)
  if (!scale) {
    return null
  }

  const plotHeight = CHART_HEIGHT - PLOT_TOP - PLOT_BOTTOM
  const gridWidth = getHourlyGridWidth(hourly.length, stepMinutes)
  const yTicks = buildTemperatureTicks(scale)
  const hasTemperature = temperatures.length > 0

  const dewPointsPlotted = hourly
    .map((entry, index) => {
      if (entry.dew_point == null) {
        return null
      }
      return {
        x: getHourlyColumnCenterX(index, stepMinutes),
        y: valueToChartY(entry.dew_point, scale, PLOT_TOP, plotHeight),
        entry,
      }
    })
    .filter((point): point is NonNullable<typeof point> => point != null)

  const tempPointsPlotted = hasTemperature
    ? hourly
        .map((entry, index) => {
          if (entry.temperature == null) {
            return null
          }
          return {
            x: getHourlyColumnCenterX(index, stepMinutes),
            y: valueToChartY(entry.temperature, scale, PLOT_TOP, plotHeight),
            entry,
          }
        })
        .filter((point): point is NonNullable<typeof point> => point != null)
    : []

  const dewPolyline = dewPointsPlotted.map((point) => `${point.x},${point.y}`).join(' ')
  const tempPolyline = tempPointsPlotted.map((point) => `${point.x},${point.y}`).join(' ')

  return (
    <div className="hourly-temp-chart">
      <svg
        viewBox={`0 0 ${gridWidth} ${CHART_HEIGHT}`}
        width={gridWidth}
        height={CHART_HEIGHT}
        className="hourly-temp-svg"
        role="img"
        aria-label="Dew point and air temperature during astronomical darkness"
        preserveAspectRatio="xMinYMid meet"
      >
        {yTicks.map((tick) => {
          const y = valueToChartY(tick, scale, PLOT_TOP, plotHeight)
          return (
            <line
              key={tick}
              x1={0}
              y1={y}
              x2={gridWidth}
              y2={y}
              className="hourly-temp-grid-line"
            />
          )
        })}

        {hasTemperature && tempPolyline && (
          <polyline points={tempPolyline} className="hourly-temp-line hourly-temp-line--air" fill="none" />
        )}

        {dewPolyline && (
          <polyline points={dewPolyline} className="hourly-temp-line hourly-temp-line--dew" fill="none" />
        )}

        {tempPointsPlotted.map((point) => (
          <circle
            key={`temp-${point.entry.at}`}
            cx={point.x}
            cy={point.y}
            r={3}
            className="hourly-temp-dot hourly-temp-dot--air"
          >
            <title>
              {`${formatHour12(point.entry.time)} — Dew ${formatTemperature(point.entry.dew_point)} · Air ${formatTemperature(point.entry.temperature)}`}
            </title>
          </circle>
        ))}

        {dewPointsPlotted.map((point) => (
          <circle
            key={`dew-${point.entry.at}`}
            cx={point.x}
            cy={point.y}
            r={3.5}
            className="hourly-temp-dot hourly-temp-dot--dew"
          >
            <title>
              {hasTemperature
                ? `${formatHour12(point.entry.time)} — Dew ${formatTemperature(point.entry.dew_point)} · Air ${formatTemperature(point.entry.temperature)}`
                : `${formatHour12(point.entry.time)} — Dew ${formatTemperature(point.entry.dew_point)}`}
            </title>
          </circle>
        ))}
      </svg>
    </div>
  )
}

export function DewPointChartAxis({ hourly }: DewPointChartProps) {
  const dewPoints = hourly
    .map((entry) => entry.dew_point)
    .filter((value): value is number => value != null)

  if (dewPoints.length === 0) {
    return null
  }

  const temperatures = hourly
    .map((entry) => entry.temperature)
    .filter((value): value is number => value != null)

  const scale = buildTemperatureScale(dewPoints, temperatures)
  if (!scale) {
    return null
  }

  const plotHeight = CHART_HEIGHT - PLOT_TOP - PLOT_BOTTOM
  const yTicks = buildTemperatureTicks(scale)

  return (
    <div className="hourly-temp-axis" aria-hidden="true">
      <span className="hourly-temp-axis-title">°F</span>
      <div className="hourly-temp-axis-ticks" style={{ height: `${CHART_HEIGHT}px` }}>
        {yTicks.map((tick) => {
          const y = valueToChartY(tick, scale, PLOT_TOP, plotHeight)
          return (
            <span
              key={tick}
              className="hourly-temp-axis-tick"
              style={{ top: `${(y / CHART_HEIGHT) * 100}%` }}
            >
              {formatTemperature(tick)}
            </span>
          )
        })}
      </div>
    </div>
  )
}
