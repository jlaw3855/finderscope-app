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
        Precip {formatPrecipitationMm(precipitation.total_mm)} · Max{' '}
        {formatPrecipitationMm(precipitation.max_hourly_mm)}/hr ·{' '}
        {formatPrecipitationProbability(precipitation.max_probability)} chance
      </p>
    )
  }

  return (
    <div className="precip-breakdown">
      <div className="precip-stat">
        <span className="precip-stat-label">Total during darkness</span>
        <span className="precip-stat-value">{formatPrecipitationMm(precipitation.total_mm)}</span>
      </div>
      <div className="precip-stat">
        <span className="precip-stat-label">Max hourly</span>
        <span className="precip-stat-value">{formatPrecipitationMm(precipitation.max_hourly_mm)}</span>
      </div>
      <div className="precip-stat">
        <span className="precip-stat-label">Peak probability</span>
        <span className="precip-stat-value">
          {formatPrecipitationProbability(precipitation.max_probability)}
        </span>
      </div>
    </div>
  )
}
