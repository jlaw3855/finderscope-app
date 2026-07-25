import { useMemo } from 'react'

import type { VisibilityWindow } from '../types/astronomy'
import type { DsoVisibilityRow } from '../types/dso-visibility'
import {
  formatMagnitude,
  formatPeakAltitude,
} from '../lib/astronomy-format'
import {
  OBSERVING_AXIS_TICKS,
  darknessSegmentsForObservingAxis,
  dsoRowColor,
  forecastAndAstroDarknessFullyOverlap,
  formatContrast,
  formatDsoLabel,
  formatDsoShortLabel,
  formatDsoType,
  mergeObservingTimelineSegments,
  mergeObservingWindows,
  observingTickLeftPercent,
  observingWindowToSegment,
} from '../lib/dso-timeline-layout'
import {
  type TimelineSegment,
  minutesToLocalHm,
} from '../lib/planet-timeline-layout'

interface DsoVisibilityTimelineProps {
  date: string
  objects: DsoVisibilityRow[]
  darknessSegments: TimelineSegment[]
  noDarkness?: boolean
  showNextDaySpilloverHint?: boolean
  timelineTestId?: string
  detailsTestId?: string
}

const UNIFIED_DARKNESS_LABEL = 'Darkness (Sun below −18°)'
const CHART_DARKNESS_LABEL = 'Darkness'
const FORECAST_DARKNESS_LABEL = 'Forecast darkness'

function formatDsoTooltip(row: DsoVisibilityRow, window: VisibilityWindow): string {
  const parts = [
    formatDsoLabel(row),
    formatDsoType(row.object_type),
    `Astronomical darkness · ${window.start} – ${window.end}`,
    row.peak_at ? `peak ${formatPeakAltitude(row.peak_altitude_deg)} at ${row.peak_at}` : null,
    row.magnitude != null ? `mag ${formatMagnitude(row.magnitude)}` : null,
    `contrast +${formatContrast(row.contrast)}`,
  ].filter(Boolean)
  return parts.join(' · ')
}

function DarknessTrack({
  segments,
  unifiedDarkness,
}: {
  segments: TimelineSegment[]
  unifiedDarkness: boolean
}) {
  const labelPrefix = unifiedDarkness ? UNIFIED_DARKNESS_LABEL : FORECAST_DARKNESS_LABEL
  return (
    <div className="planet-timeline-track">
      {segments.map((segment) => (
        <span
          key={`${segment.startMinutes}-${segment.endMinutes}`}
          className="planet-timeline-darkness"
          data-testid="dso-timeline-darkness"
          style={{
            left: `${segment.leftPercent}%`,
            width: `${segment.widthPercent}%`,
          }}
          title={`${labelPrefix} · ${minutesToLocalHm(segment.startMinutes)} – ${minutesToLocalHm(segment.endMinutes)}`}
        />
      ))}
    </div>
  )
}

function DsoWindowSegments({
  row,
  rowIndex,
  windows,
}: {
  row: DsoVisibilityRow
  rowIndex: number
  windows: VisibilityWindow[]
}) {
  const color = dsoRowColor(rowIndex)
  const mergedWindows = mergeObservingWindows(windows)

  return mergedWindows.flatMap((window) => {
    const segment = observingWindowToSegment(window.start, window.end)
    if (!segment) {
      return []
    }
    const tooltip = formatDsoTooltip(row, window)
    return (
      <span
        key={`${row.id}-${window.start}-${window.end}`}
        className="planet-timeline-segment planet-timeline-segment--astronomical"
        data-testid="dso-timeline-segment"
        data-twilight="astronomical"
        style={{
          left: `${segment.leftPercent}%`,
          width: `${segment.widthPercent}%`,
          backgroundColor: color,
        }}
        title={tooltip}
        aria-label={tooltip}
      />
    )
  })
}

export function DsoVisibilityTimeline({
  date,
  objects,
  darknessSegments,
  noDarkness = false,
  showNextDaySpilloverHint = false,
  timelineTestId = 'dso-visibility-timeline',
}: DsoVisibilityTimelineProps) {
  const observingDarknessSegments = useMemo(
    () =>
      mergeObservingTimelineSegments(darknessSegmentsForObservingAxis(darknessSegments)),
    [darknessSegments],
  )
  const unifiedDarkness = useMemo(
    () => forecastAndAstroDarknessFullyOverlap(objects, darknessSegments),
    [darknessSegments, objects],
  )
  const darknessRowLabel = unifiedDarkness ? CHART_DARKNESS_LABEL : FORECAST_DARKNESS_LABEL

  return (
    <div
      className="planet-timeline dso-timeline"
      data-testid={timelineTestId}
      data-unified-darkness={unifiedDarkness ? 'true' : 'false'}
      role="img"
      aria-label={`Deep sky visibility timeline for ${date}, 6 PM to 6 AM`}
    >
      <div className="planet-timeline-axis-row dso-timeline-axis-row">
        <div className="planet-timeline-label planet-timeline-label--axis" aria-hidden="true" />
        <div className="planet-timeline-axis" aria-hidden="true">
          {OBSERVING_AXIS_TICKS.map((tick) => (
            <span
              key={tick.extendedMinutes}
              className="planet-timeline-axis-tick"
              style={{ left: `${observingTickLeftPercent(tick.extendedMinutes)}%` }}
            >
              {tick.label}
            </span>
          ))}
        </div>
      </div>

      <div className="planet-timeline-rows">
        <div className="planet-timeline-row planet-timeline-row--darkness">
          <div className="planet-timeline-label">
            <span
              className={`planet-timeline-swatch ${
                unifiedDarkness
                  ? 'planet-timeline-swatch--astronomical'
                  : 'planet-timeline-swatch--darkness'
              }`}
              aria-hidden="true"
            />
            <span className="dso-timeline-darkness-label">{darknessRowLabel}</span>
          </div>
          <DarknessTrack segments={observingDarknessSegments} unifiedDarkness={unifiedDarkness} />
        </div>

        {objects.map((row, index) => (
          <div key={row.id} className="planet-timeline-row">
            <div className="planet-timeline-label planet-timeline-label--dso">
              <span
                className="planet-timeline-swatch"
                style={{ backgroundColor: dsoRowColor(index) }}
                aria-hidden="true"
              />
              <span className="dso-timeline-name dso-timeline-name--short">
                {formatDsoShortLabel(row)}
              </span>
            </div>
            <div className="planet-timeline-track">
              <DsoWindowSegments
                row={row}
                rowIndex={index}
                windows={row.windows_astronomical}
              />
            </div>
          </div>
        ))}
      </div>

      {noDarkness && (
        <p className="muted planet-timeline-note">No astronomical darkness on this calendar day.</p>
      )}
      {!noDarkness && showNextDaySpilloverHint && (
        <p className="muted planet-timeline-note">
          Pre-dawn darkness from this night continues on the next calendar day in the forecast.
        </p>
      )}
      <p className="muted planet-timeline-note dso-timeline-footnote">
        6 PM–6 AM · Astronomical darkness only (Sun below −18°)
      </p>
    </div>
  )
}

export function DsoDayDetails({
  objects,
  detailsTestId = 'dso-visibility-details',
}: {
  objects: DsoVisibilityRow[]
  detailsTestId?: string
}) {
  return (
    <ul className="planet-timeline-details dso-timeline-details" data-testid={detailsTestId}>
      {objects.map((row) => (
        <li key={row.id} className="planet-timeline-detail-row" data-testid="dso-visibility-detail">
          <span className="planet-timeline-detail-name">{formatDsoLabel(row)}</span>
          <span className="muted">{formatDsoType(row.object_type)}</span>
          <span className={row.visible ? 'planet-timeline-detail-visible' : 'muted'}>
            {row.visible ? 'Visible' : 'Not visible'}
          </span>
          {row.visible && (
            <span className="planet-timeline-detail-meta muted">
              peak {formatPeakAltitude(row.peak_altitude_deg)}
              {row.peak_at ? ` at ${row.peak_at}` : ''}
              {' · mag '}
              {formatMagnitude(row.magnitude)}
              {' · contrast +'}
              {formatContrast(row.contrast)}
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}
