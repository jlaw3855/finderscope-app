import type { CloudCoverBreakdown } from '../types/forecast'
import { formatCloudCover } from '../lib/weather-format'

interface CloudBreakdownProps {
  cloud: CloudCoverBreakdown
  compact?: boolean
}

export function CloudBreakdown({ cloud, compact = false }: CloudBreakdownProps) {
  const layers = [
    { key: 'low', label: 'Low', value: cloud.low, className: 'cloud-layer-low' },
    { key: 'mid', label: 'Mid', value: cloud.mid, className: 'cloud-layer-mid' },
    { key: 'high', label: 'High', value: cloud.high, className: 'cloud-layer-high' },
  ]

  if (compact) {
    return (
      <div className="cloud-breakdown compact">
        <span className="cloud-breakdown-total">Clouds {formatCloudCover(cloud.total)}</span>
        <span className="cloud-breakdown-layers">
          {layers.map((layer) => (
            <span key={layer.key}>
              {layer.label} {formatCloudCover(layer.value)}
            </span>
          ))}
        </span>
      </div>
    )
  }

  return (
    <div className="cloud-breakdown">
      <div className="cloud-breakdown-header">
        <span>Cloud cover {formatCloudCover(cloud.total)}</span>
      </div>
      <div className="cloud-layer-bars">
        {layers.map((layer) => (
          <div key={layer.key} className="cloud-layer-row">
            <span className="cloud-layer-label">{layer.label}</span>
            <div className="cloud-layer-track">
              <div
                className={`cloud-layer-fill ${layer.className}`}
                style={{ width: `${Math.min(layer.value ?? 0, 100)}%` }}
              />
            </div>
            <span className="cloud-layer-value">{formatCloudCover(layer.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
