import type { HourlyScore } from '../types/forecast'
import { formatHour12, formatTemperature } from '../lib/weather-format'

interface DewPointChartProps {
  hourly: HourlyScore[]
}

const CHART_WIDTH = 640
const CHART_HEIGHT = 160
const PADDING = { top: 16, right: 16, bottom: 28, left: 40 }

export function DewPointChart({ hourly }: DewPointChartProps) {
  const dewPoints = hourly
    .map((entry) => entry.dew_point)
    .filter((value): value is number => value != null)

  if (dewPoints.length === 0) {
    return null
  }

  const temperatures = hourly
    .map((entry) => entry.temperature)
    .filter((value): value is number => value != null)

  const allValues = [...dewPoints, ...temperatures]
  const minValue = Math.floor(Math.min(...allValues) - 1)
  const maxValue = Math.ceil(Math.max(...allValues) + 1)
  const valueRange = Math.max(maxValue - minValue, 1)

  const plotWidth = CHART_WIDTH - PADDING.left - PADDING.right
  const plotHeight = CHART_HEIGHT - PADDING.top - PADDING.bottom

  const points = hourly
    .filter((entry) => entry.dew_point != null)
    .map((entry, index, filtered) => {
      const x =
        PADDING.left + (index / Math.max(filtered.length - 1, 1)) * plotWidth
      const y =
        PADDING.top +
        plotHeight -
        (((entry.dew_point as number) - minValue) / valueRange) * plotHeight
      return { x, y, entry }
    })

  const polyline = points.map((point) => `${point.x},${point.y}`).join(' ')

  const yTicks = [minValue, minValue + valueRange / 2, maxValue]

  return (
    <div className="dew-point-chart">
      <h3>Dew point during darkness</h3>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="dew-point-svg"
        role="img"
        aria-label="Dew point curve during astronomical darkness"
      >
        {yTicks.map((tick) => {
          const y =
            PADDING.top +
            plotHeight -
            ((tick - minValue) / valueRange) * plotHeight
          return (
            <g key={tick}>
              <line
                x1={PADDING.left}
                y1={y}
                x2={CHART_WIDTH - PADDING.right}
                y2={y}
                className="dew-grid-line"
              />
              <text x={4} y={y + 4} className="dew-axis-label">
                {formatTemperature(tick)}
              </text>
            </g>
          )
        })}

        <polyline points={polyline} className="dew-point-line" fill="none" />

        {points.map((point) => (
          <g key={point.entry.at}>
            <circle cx={point.x} cy={point.y} r={3.5} className="dew-point-dot" />
            <title>
              {`${formatHour12(point.entry.time)}: dew ${formatTemperature(point.entry.dew_point)}`}
            </title>
          </g>
        ))}

        {points.map((point, index) =>
          index % 2 === 0 || index === points.length - 1 ? (
            <text
              key={`${point.entry.at}-label`}
              x={point.x}
              y={CHART_HEIGHT - 6}
              textAnchor="middle"
              className="dew-time-label"
            >
              {formatHour12(point.entry.time)}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  )
}
