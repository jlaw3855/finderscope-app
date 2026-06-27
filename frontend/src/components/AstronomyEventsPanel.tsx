import type { AstronomyResponse } from '../types/astronomy'
import { NAKED_EYE_PLANETS, TELESCOPE_PLANETS } from '../types/astronomy'
import {
  altitudeBarPercent,
  formatEventCategory,
  formatEventDate,
  formatMagnitude,
  formatNightColumnDate,
  formatPeakAltitude,
  formatVisibilityWindows,
  eventCategoryClass,
  sortEventsByStart,
} from '../lib/astronomy-format'

interface AstronomyEventsPanelProps {
  timezone: string
  data: AstronomyResponse | null
  loading: boolean
  error: string | null
}

const ALL_PLANET_ROWS = [...NAKED_EYE_PLANETS, ...TELESCOPE_PLANETS]

export function AstronomyEventsPanel({
  timezone,
  data,
  loading,
  error,
}: AstronomyEventsPanelProps) {
  const events = sortEventsByStart(data?.events ?? [])
  const planetDays = data?.planet_visibility ?? []

  return (
    <section className="panel astronomy-panel" data-testid="astronomy-panel">
      <header className="astronomy-panel-header">
        <h2>Astronomy</h2>
        <p className="muted">Next 30 days of events and 7-day planet visibility for this location.</p>
      </header>

      {loading && <p className="muted astronomy-status">Loading astronomy data…</p>}
      {error && (
        <p className="error-text astronomy-status" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && data && (
        <>
          <section className="astronomy-section" aria-labelledby="astronomy-events-heading">
            <h3 id="astronomy-events-heading">Events timeline</h3>
            {events.length === 0 ? (
              <p className="muted astronomy-empty" data-testid="astronomy-events-empty">
                No notable astronomy events in the next 30 days.
              </p>
            ) : (
              <ol className="astronomy-timeline" data-testid="astronomy-events-list">
                {events.map((event) => (
                  <li
                    key={event.id}
                    className={`astronomy-event ${eventCategoryClass(event.category)}`}
                    data-testid="astronomy-event"
                  >
                    <div className="astronomy-event-marker" aria-hidden="true" />
                    <div className="astronomy-event-card">
                      <div className="astronomy-event-header">
                        <span className="astronomy-event-category">
                          {formatEventCategory(event.category)}
                        </span>
                        {!event.visible_locally && (
                          <span className="astronomy-visibility-badge">Not visible locally</span>
                        )}
                      </div>
                      <h4>{event.title}</h4>
                      <p className="astronomy-event-time muted">
                        {formatEventDate(event.start_at, timezone)}
                      </p>
                      <p className="astronomy-event-description">{event.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section className="astronomy-section" aria-labelledby="planet-visibility-heading">
            <h3 id="planet-visibility-heading">Planet visibility</h3>
            <p className="muted astronomy-section-note">
              Visible when above the horizon at any time on each forecast night (local time).
            </p>
            <div className="planet-visibility-scroll">
              <table className="planet-visibility-table" data-testid="planet-visibility-table">
                <thead>
                  <tr>
                    <th scope="col">Planet</th>
                    {planetDays.map((day) => (
                      <th key={day.date} scope="col">
                        {formatNightColumnDate(day.date)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ALL_PLANET_ROWS.map((planetName) => {
                    const isTelescope = TELESCOPE_PLANETS.includes(
                      planetName as (typeof TELESCOPE_PLANETS)[number],
                    )
                    return (
                      <tr
                        key={planetName}
                        className={isTelescope ? 'planet-row--telescope' : undefined}
                      >
                        <th scope="row">{planetName}</th>
                        {planetDays.map((day) => {
                          const row = day.planets.find((planet) => planet.body === planetName)
                          if (!row) {
                            return (
                              <td key={`${day.date}-${planetName}`} className="planet-cell">
                                —
                              </td>
                            )
                          }
                          return (
                            <td
                              key={`${day.date}-${planetName}`}
                              className={`planet-cell ${row.visible ? 'planet-cell--visible' : 'planet-cell--hidden'}`}
                              data-testid="planet-visibility-cell"
                            >
                              <span className="planet-visible-label">
                                {row.visible ? 'Visible' : 'Not visible'}
                              </span>
                              {row.visible && (
                                <>
                                  <span className="planet-windows">
                                    {formatVisibilityWindows(row.windows)}
                                  </span>
                                  <span
                                    className="planet-altitude-bar"
                                    aria-hidden="true"
                                    style={{ width: `${altitudeBarPercent(row.peak_altitude_deg)}%` }}
                                  />
                                  <span className="planet-peak muted">
                                    Peak {formatPeakAltitude(row.peak_altitude_deg)}
                                    {row.peak_at ? ` at ${row.peak_at}` : ''}
                                    {' · mag '}
                                    {formatMagnitude(row.magnitude)}
                                  </span>
                                </>
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </section>
  )
}
