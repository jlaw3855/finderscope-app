import { memo, useMemo } from 'react'

import type { AstronomyResponse } from '../types/astronomy'
import {
  formatEventCategory,
  formatEventDate,
  formatNightColumnDate,
  formatSubjectAliases,
  formatSubjectInterest,
  formatSubjectTypes,
  eventCategoryClass,
  sortEventsByStart,
} from '../lib/astronomy-format'
import {
  darknessSegmentsForCalendarDay,
} from '../lib/planet-timeline-layout'
import type { NightForecast, TimeWindow } from '../types/forecast'
import {
  PlanetDayDetails,
  PlanetTimelineLegend,
  PlanetVisibilityTimeline,
} from './PlanetVisibilityTimeline'

interface AstronomyEventsPanelProps {
  timezone: string
  nights: NightForecast[]
  priorDayDarkWindow?: TimeWindow | null
  data: AstronomyResponse | null
  loading: boolean
  error: string | null
  selectedNightDate?: string | null
  onSelectedNightDateChange?: (date: string) => void
}

function AstronomyEventsPanelComponent({
  timezone,
  nights,
  priorDayDarkWindow,
  data,
  loading,
  error,
  selectedNightDate,
  onSelectedNightDateChange,
}: AstronomyEventsPanelProps) {
  const events = useMemo(() => sortEventsByStart(data?.events ?? []), [data?.events])
  const availableDates = useMemo(
    () => data?.planet_visibility.map((day) => day.date) ?? [],
    [data?.planet_visibility],
  )
  const planetDays = data?.planet_visibility ?? []

  const selectedDate =
    selectedNightDate && availableDates.includes(selectedNightDate)
      ? selectedNightDate
      : availableDates[0] ?? ''

  const selectedDay = planetDays.find((day) => day.date === selectedDate)
  const selectedNight = nights.find((night) => night.date === selectedDate)
  const firstForecastDate = nights[0]?.date
  const darknessSegments = useMemo(
    () =>
      selectedDate
        ? darknessSegmentsForCalendarDay(selectedDate, nights, {
            priorDayDarkWindow,
            firstForecastDate,
          })
        : [],
    [firstForecastDate, nights, priorDayDarkWindow, selectedDate],
  )
  const showNextDaySpilloverHint =
    availableDates.length > 0 &&
    selectedDate === availableDates[0] &&
    Boolean(selectedNight?.dark_window && !selectedNight.no_darkness)

  return (
    <section className="panel astronomy-panel" data-testid="astronomy-panel">
      <header className="astronomy-panel-header">
        <h2>Astronomy</h2>
        <p className="muted">
          Next 3 months of events and a 24-hour planet visibility timeline with astronomical darkness
          overlay.
        </p>
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
                No notable astronomy events in the next 3 months.
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
                      {event.subjects.length > 0 && (
                        <ul className="astronomy-event-subjects" data-testid="astronomy-event-subjects">
                          {event.subjects.map((subject) => {
                            const interest = formatSubjectInterest(subject.interest)
                            const aliases = formatSubjectAliases(subject)
                            return (
                              <li key={`${event.id}-${subject.query}`} className="astronomy-event-subject">
                                <span className="astronomy-event-subject-type">
                                  {formatSubjectTypes(subject)}
                                </span>
                                {interest && (
                                  <span className="astronomy-event-subject-interest muted">{interest}</span>
                                )}
                                {aliases && (
                                  <span className="astronomy-event-subject-aliases muted">{aliases}</span>
                                )}
                              </li>
                            )
                          })}
                        </ul>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section className="astronomy-section" aria-labelledby="planet-visibility-heading">
            <h3 id="planet-visibility-heading">Planet visibility</h3>
            <p className="muted astronomy-section-note">
              Select a forecast night to view planet visibility when the Sun is below civil twilight
              (−6°) and astronomical twilight (−18°). Shaded bands show forecast astronomical darkness
              clipped to that day; pre-dawn darkness from the prior night appears on the following day.
            </p>

            {availableDates.length > 0 && selectedDay && (
              <>
                <div className="planet-timeline-controls">
                  <label htmlFor="planet-timeline-date-select">
                    Forecast night
                    <select
                      id="planet-timeline-date-select"
                      className="planet-timeline-select"
                      data-testid="planet-timeline-date-select"
                      value={selectedDate}
                      onChange={(event) => onSelectedNightDateChange?.(event.target.value)}
                    >
                      {availableDates.map((date) => (
                        <option key={date} value={date}>
                          {formatNightColumnDate(date)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <PlanetVisibilityTimeline
                  date={selectedDate}
                  planets={selectedDay.planets}
                  darknessSegments={darknessSegments}
                  noDarkness={selectedNight?.no_darkness === true}
                  showNextDaySpilloverHint={showNextDaySpilloverHint}
                />

                <PlanetTimelineLegend />
                <PlanetDayDetails planets={selectedDay.planets} />
              </>
            )}
          </section>
        </>
      )}
    </section>
  )
}

export const AstronomyEventsPanel = memo(AstronomyEventsPanelComponent)
