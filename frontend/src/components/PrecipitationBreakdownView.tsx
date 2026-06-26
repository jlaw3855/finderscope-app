import type { PrecipitationBreakdown } from '../types/forecast'
import {
  formatPrecipitationMm,
  formatPrecipitationProbability,
} from '../lib/weather-format'

interface PrecipitationBreakdownViewProps {
  precipitation: PrecipitationBreakdown
  compact?: boolean
}

export function PrecipitationBreakdownView({
  precipitation,
  compact = false,
}: PrecipitationBreakdownViewProps) {
  if (compact) {
    return (
      <p className="precip-breakdown compact">
        Rainfall: {formatPrecipitationMm(precipitation.total_mm)} total ·{' '}
        {formatPrecipitationMm(precipitation.max_hourly_mm)} max/hr ·{' '}
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
          <span className="precip-stat-value">{formatPrecipitationMm(precipitation.total_mm)}</span>
        </div>
        <div className="precip-stat">
          <span className="precip-stat-label">Heaviest hourly rainfall</span>
          <span className="precip-stat-value">{formatPrecipitationMm(precipitation.max_hourly_mm)}</span>
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
