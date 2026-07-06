import { describe, expect, it } from 'vitest'

import type { NightForecast } from '../types/forecast'
import {
  darknessSegmentsForCalendarDay,
  parseLocalHm,
} from './planet-timeline-layout'
import {
  OBSERVING_AXIS_SPAN,
  OBSERVING_AXIS_START_MINUTES,
  astroUnionSegmentsFromObjects,
  darknessSegmentsForObservingAxis,
  forecastAndAstroDarknessFullyOverlap,
  formatDsoShortLabel,
  mergeObservingTimelineSegments,
  mergeObservingWindows,
  observingTickLeftPercent,
  observingWindowToSegment,
  toExtendedMinutes,
} from './dso-timeline-layout'

function night(
  date: string,
  darkWindow: { start: string; end: string } | null,
  noDarkness = false,
): NightForecast {
  return {
    date,
    rating: 'Good',
    score: 80,
    moon_phase: 'FULL_MOON',
    moon_illumination: 50,
    cloud_cover: { total: 0, low: 0, mid: 0, high: 0 },
    precipitation: { total_mm: 0, max_hourly_mm: 0, max_probability: 0 },
    dark_window: darkWindow,
    best_hours: [],
    hourly: [],
    no_darkness: noDarkness,
    meteor_showers: [],
  }
}

describe('dso-timeline-layout', () => {
  it('maps morning calendar minutes into the extended observing timeline', () => {
    expect(toExtendedMinutes(parseLocalHm('03:29'))).toBe(parseLocalHm('03:29') + 24 * 60)
    expect(toExtendedMinutes(parseLocalHm('21:04'))).toBe(parseLocalHm('21:04'))
  })

  it('maps evening and pre-dawn windows onto the 6 PM to 6 AM axis', () => {
    const evening = observingWindowToSegment('21:04', '23:59')
    const morning = observingWindowToSegment('00:00', '03:29')

    expect(evening).not.toBeNull()
    expect(morning).not.toBeNull()
    expect(evening!.leftPercent).toBeCloseTo(((21 * 60 + 4 - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100, 2)
    expect(morning!.leftPercent).toBeCloseTo(50, 2)
    expect(evening!.leftPercent + evening!.widthPercent).toBeLessThanOrEqual(morning!.leftPercent + 0.01)
  })

  it('clips windows outside the fixed observing band', () => {
    expect(observingWindowToSegment('12:00', '14:00')).toBeNull()
    expect(observingWindowToSegment('17:00', '18:30')).toEqual({
      startMinutes: OBSERVING_AXIS_START_MINUTES,
      endMinutes: 18 * 60 + 30,
      leftPercent: 0,
      widthPercent: (30 / OBSERVING_AXIS_SPAN) * 100,
    })
  })

  it('remaps forecast darkness segments onto the observing axis', () => {
    const nights = [night('2025-06-20', { start: '21:30', end: '04:45' })]
    const calendarSegments = darknessSegmentsForCalendarDay('2025-06-20', nights)
    const observingSegments = darknessSegmentsForObservingAxis(calendarSegments)

    expect(observingSegments).toHaveLength(1)
    expect(observingSegments[0].leftPercent).toBeCloseTo(
      ((parseLocalHm('21:30') - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
      2,
    )
    expect(observingSegments[0].widthPercent).toBeCloseTo(
      ((24 * 60 - parseLocalHm('21:30')) / OBSERVING_AXIS_SPAN) * 100,
      2,
    )
  })

  it('places observing axis ticks from 6 PM through 6 AM', () => {
    expect(observingTickLeftPercent(18 * 60)).toBe(0)
    expect(observingTickLeftPercent(24 * 60)).toBe(50)
    expect(observingTickLeftPercent(30 * 60)).toBe(100)
  })

  it('merges pre-dawn and evening darkness on the observing axis', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const calendarSegments = darknessSegmentsForCalendarDay('2025-06-21', nights)
    const observingSegments = darknessSegmentsForObservingAxis(calendarSegments)

    expect(observingSegments).toHaveLength(2)
    expect(observingSegments[0].startMinutes).toBe(toExtendedMinutes(0))
    expect(observingSegments[1].startMinutes).toBe(parseLocalHm('21:30'))
  })

  it('maps pre-dawn-only darkness onto the observing axis', () => {
    const nights = [night('2025-06-20', { start: '01:00', end: '05:00' })]
    const calendarSegments = darknessSegmentsForCalendarDay('2025-06-20', nights)
    const observingSegments = darknessSegmentsForObservingAxis(calendarSegments)

    expect(observingSegments).toHaveLength(1)
    expect(observingSegments[0].leftPercent).toBeCloseTo(
      ((24 * 60 + 60 - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
      2,
    )
  })

  it('formatDsoShortLabel returns catalog id only', () => {
    expect(formatDsoShortLabel({ name: 'NGC7000' })).toBe('NGC7000')
  })

  it('mergeObservingWindows joins midnight-split segments', () => {
    const merged = mergeObservingWindows([
      { start: '22:33', end: '23:59' },
      { start: '00:00', end: '03:29' },
    ])

    expect(merged).toEqual([{ start: '22:33', end: '03:29' }])

    const segment = observingWindowToSegment(merged[0].start, merged[0].end)
    expect(segment).not.toBeNull()
    expect(segment!.leftPercent).toBeCloseTo(
      ((22 * 60 + 33 - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
      2,
    )
    expect(segment!.leftPercent + segment!.widthPercent).toBeGreaterThan(50)
  })

  it('mergeObservingWindows keeps non-adjacent windows separate', () => {
    const merged = mergeObservingWindows([
      { start: '20:00', end: '20:30' },
      { start: '23:00', end: '23:30' },
    ])

    expect(merged).toHaveLength(2)
  })

  it('mergeObservingTimelineSegments joins split darkness bands on the observing axis', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const calendarSegments = darknessSegmentsForCalendarDay('2025-06-21', nights)
    const observingSegments = darknessSegmentsForObservingAxis(calendarSegments)
    const merged = mergeObservingTimelineSegments(observingSegments)

    expect(observingSegments.length).toBeGreaterThan(1)
    expect(merged).toHaveLength(1)
    expect(merged[0].leftPercent).toBeCloseTo(
      ((parseLocalHm('21:30') - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
      2,
    )
  })

  it('forecastAndAstroDarknessFullyOverlap detects matching spans', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const calendarSegments = darknessSegmentsForCalendarDay('2025-06-21', nights)
    const objects = [{ windows_astronomical: [{ start: '21:30', end: '04:45' }] }]

    expect(forecastAndAstroDarknessFullyOverlap(objects, calendarSegments)).toBe(true)
    expect(
      forecastAndAstroDarknessFullyOverlap(
        [{ windows_astronomical: [{ start: '22:00', end: '03:00' }] }],
        calendarSegments,
      ),
    ).toBe(false)
  })

  it('astroUnionSegmentsFromObjects merges object windows into one span', () => {
    const union = astroUnionSegmentsFromObjects([
      {
        windows_astronomical: [
          { start: '22:33', end: '23:59' },
          { start: '00:00', end: '03:29' },
        ],
      },
      {
        windows_astronomical: [
          { start: '22:00', end: '23:59' },
          { start: '00:00', end: '04:00' },
        ],
      },
    ])

    expect(union).toHaveLength(1)
  })
})
