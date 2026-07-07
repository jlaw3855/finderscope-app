import type { PlanetVisibilityRow, VisibilityWindow } from '../types/astronomy'
import {
  formatMagnitude,
  formatPeakAltitude,
  formatVisibilityWindows,
} from '../lib/astronomy-format'
import {
  ALL_PLANET_ORDER,
  PLANET_COLORS,
  TELESCOPE_PLANET_ORDER,
  TIMELINE_AXIS_HOURS,
  type TimelineSegment,
  formatTimelineAxisLabel,
  minutesToLocalHm,
  windowToSegment,
} from '../lib/planet-timeline-layout'

interface PlanetVisibilityTimelineProps {
  date: string
  planets: PlanetVisibilityRow[]
  darknessSegments: TimelineSegment[]
  noDarkness?: boolean
  showNextDaySpilloverHint?: boolean
}

function formatDarknessLabel(segment: TimelineSegment): string {
  return `Astronomical darkness · ${minutesToLocalHm(segment.startMinutes)} – ${minutesToLocalHm(segment.endMinutes)}`
}

function formatPlanetTooltip(
  row: PlanetVisibilityRow,
  window: VisibilityWindow,
  twilight: 'civil' | 'astronomical',
): string {
  const twilightLabel = twilight === 'civil' ? 'civil twilight' : 'astronomical darkness'
  const parts = [
    row.body,
    `${twilightLabel} · ${window.start} – ${window.end}`,
    row.peak_at ? `peak ${formatPeakAltitude(row.peak_altitude_deg)} at ${row.peak_at}` : null,
    row.magnitude != null ? `mag ${formatMagnitude(row.magnitude)}` : null,
  ].filter(Boolean)
  return parts.join(' · ')
}

function DarknessTrack({ segments }: { segments: TimelineSegment[] }) {
  return (
    <div className="planet-timeline-track">
      {segments.map((segment) => (
        <span
          key={`${segment.startMinutes}-${segment.endMinutes}`}
          className="planet-timeline-darkness"
          data-testid="planet-timeline-darkness"
          style={{
            left: `${segment.leftPercent}%`,
            width: `${segment.widthPercent}%`,
          }}
          title={formatDarknessLabel(segment)}
        />
      ))}
    </div>
  )
}

function PlanetWindowSegments({
  row,
  planetName,
  windows,
  twilight,
}: {
  row: PlanetVisibilityRow
  planetName: string
  windows: VisibilityWindow[]
  twilight: 'civil' | 'astronomical'
}) {
  return windows.map((window) => {
    const segment = windowToSegment(window.start, window.end)
    const className =
      twilight === 'civil'
        ? 'planet-timeline-segment planet-timeline-segment--civil'
        : 'planet-timeline-segment planet-timeline-segment--astronomical'
    return (
      <span
        key={`${planetName}-${twilight}-${window.start}-${window.end}`}
        className={className}
        data-testid="planet-timeline-segment"
        data-twilight={twilight}
        style={{
          left: `${segment.leftPercent}%`,
          width: `${segment.widthPercent}%`,
          backgroundColor: PLANET_COLORS[planetName],
        }}
        title={formatPlanetTooltip(row, window, twilight)}
        aria-label={formatPlanetTooltip(row, window, twilight)}
      />
    )
  })
}

export function PlanetVisibilityTimeline({
  date,
  planets,
  darknessSegments,
  noDarkness = false,
  showNextDaySpilloverHint = false,
}: PlanetVisibilityTimelineProps) {
  const planetByName = Object.fromEntries(planets.map((planet) => [planet.body, planet]))

  return (
    <div
      className="planet-timeline"
      data-testid="planet-visibility-timeline"
      role="img"
      aria-label={`Planet visibility timeline for ${date}`}
    >
      <div className="planet-timeline-axis-row">
        <div className="planet-timeline-label planet-timeline-label--axis" aria-hidden="true" />
        <div className="planet-timeline-axis" aria-hidden="true">
          {TIMELINE_AXIS_HOURS.map((hour) => (
            <span
              key={hour}
              className="planet-timeline-axis-tick"
              style={{ left: `${(hour / 24) * 100}%` }}
            >
              {formatTimelineAxisLabel(hour)}
            </span>
          ))}
        </div>
      </div>

      <div className="planet-timeline-rows">
        <div className="planet-timeline-row planet-timeline-row--darkness">
          <div className="planet-timeline-label">
            <span
              className="planet-timeline-swatch planet-timeline-swatch--darkness"
              aria-hidden="true"
            />
            Darkness
          </div>
          <DarknessTrack segments={darknessSegments} />
        </div>

        {ALL_PLANET_ORDER.map((planetName) => {
          const row = planetByName[planetName]
          const isTelescope = TELESCOPE_PLANET_ORDER.includes(
            planetName as (typeof TELESCOPE_PLANET_ORDER)[number],
          )
          return (
            <div
              key={planetName}
              className={`planet-timeline-row${isTelescope ? ' planet-timeline-row--telescope' : ''}`}
            >
              <div className="planet-timeline-label">
                <span
                  className="planet-timeline-swatch"
                  style={{ backgroundColor: PLANET_COLORS[planetName] }}
                  aria-hidden="true"
                />
                {planetName}
              </div>
              <div className="planet-timeline-track">
                {row && (
                  <>
                    <PlanetWindowSegments
                      row={row}
                      planetName={planetName}
                      windows={row.windows_civil}
                      twilight="civil"
                    />
                    <PlanetWindowSegments
                      row={row}
                      planetName={planetName}
                      windows={row.windows_astronomical}
                      twilight="astronomical"
                    />
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {noDarkness && (
        <p className="muted planet-timeline-note">No astronomical darkness on this calendar day.</p>
      )}
      {!noDarkness && showNextDaySpilloverHint && (
        <p className="muted planet-timeline-note">
          Pre-dawn darkness from this night continues on the next calendar day in the forecast.
        </p>
      )}
    </div>
  )
}

export function PlanetDayDetails({ planets }: { planets: PlanetVisibilityRow[] }) {
  return (
    <ul className="planet-timeline-details" data-testid="planet-visibility-details">
      {ALL_PLANET_ORDER.map((planetName) => {
        const row = planets.find((planet) => planet.body === planetName)
        if (!row) {
          return null
        }
        return (
          <li key={planetName} className="planet-timeline-detail-row" data-testid="planet-visibility-detail">
            <span className="planet-timeline-detail-name">{planetName}</span>
            <span className={row.visible ? 'planet-timeline-detail-visible' : 'muted'}>
              {row.visible ? 'Visible' : 'Not visible'}
            </span>
            {row.visible && (
              <span className="planet-timeline-detail-meta muted">
                {formatVisibilityWindows(row.windows_civil, row.windows_astronomical)}
                {' · peak '}
                {formatPeakAltitude(row.peak_altitude_deg)}
                {row.peak_at ? ` at ${row.peak_at}` : ''}
                {' · mag '}
                {formatMagnitude(row.magnitude)}
              </span>
            )}
          </li>
        )
      })}
    </ul>
  )
}
