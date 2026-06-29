import type { PrecipitationBreakdown } from '../types/forecast'
import { formatPrecipitationProbability } from '../lib/weather-format'
import { useWeatherFormat } from '../hooks/useWeatherFormat'

interface PrecipitationBreakdownViewProps {
  precipitation: PrecipitationBreakdown
  compact?: boolean
}

export function PrecipitationBreakdownView({
  precipitation,
  compact = false,
}: PrecipitationBreakdownViewProps) {
  const fmt = useWeatherFormat()

  if (compact) {
    return (
      <p className="precip-breakdown compact">
        Rainfall: {fmt.formatPrecipitation(precipitation.total_mm)} total ·{' '}
        {fmt.formatPrecipitation(precipitation.max_hourly_mm)} max/hr ·{' '}
        {formatPrecipitationProbability(precipitation.max_probability)} chance of rain
      </p>
    )
  }

  return (
    <div className="precip-breakdown">
      <div className="precip-breakdown-header">Precipitation summary</div>
      <div className="precip-breakdown-stats">
        <div className="precip-stat">
          <span className="precip-stat-label">Total precipitation during darkness</span>
          <span className="precip-stat-value">{fmt.formatPrecipitation(precipitation.total_mm)}</span>
        </div>
        <div className="precip-stat">
          <span className="precip-stat-label">Heaviest hourly rainfall</span>
          <span className="precip-stat-value">{fmt.formatPrecipitation(precipitation.max_hourly_mm)}</span>
        </div>
        <div className="precip-stat">
          <span className="precip-stat-label">Highest chance of precipitation</span>
          <span className="precip-stat-value">
            {formatPrecipitationProbability(precipitation.max_probability)}
          </span>
        </div>
      </div>
    </div>
  )
}
