import { describe, expect, it } from 'vitest'

import type { NightForecast } from '../types/forecast'
import {
  addCalendarDays,
  darknessSegmentsForCalendarDay,
  formatTimelineAxisLabel,
  parseLocalHm,
  previousForecastNight,
  segmentFromMinutes,
  windowToSegment,
} from './planet-timeline-layout'

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

describe('planet-timeline-layout', () => {
  it('parses local HH:MM into minutes', () => {
    expect(parseLocalHm('21:30')).toBe(21 * 60 + 30)
    expect(parseLocalHm('04:45')).toBe(4 * 60 + 45)
  })

  it('maps visibility windows to segment percentages', () => {
    const segment = windowToSegment('07:27', '21:58')
    expect(segment.leftPercent).toBeCloseTo((7 * 60 + 27) / (24 * 60) * 100, 2)
    expect(segment.widthPercent).toBeCloseTo(((21 * 60 + 58) - (7 * 60 + 27)) / (24 * 60) * 100, 2)
  })

  it('clips evening darkness when the window crosses midnight', () => {
    const nights = [night('2025-06-20', { start: '21:30', end: '04:45' })]
    const segments = darknessSegmentsForCalendarDay('2025-06-20', nights)

    expect(segments).toHaveLength(1)
    expect(segments[0].startMinutes).toBe(parseLocalHm('21:30'))
    expect(segments[0].endMinutes).toBe(24 * 60)
  })

  it('adds pre-dawn darkness spillover from the previous forecast night', () => {
    const nights = [night('2025-06-20', { start: '21:30', end: '04:45' })]
    const segments = darknessSegmentsForCalendarDay('2025-06-21', nights)

    expect(segments).toHaveLength(1)
    expect(segments[0].startMinutes).toBe(0)
    expect(segments[0].endMinutes).toBe(parseLocalHm('04:45'))
  })

  it('merges pre-dawn and evening darkness on the same calendar day', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const segments = darknessSegmentsForCalendarDay('2025-06-21', nights)

    expect(segments).toHaveLength(2)
    expect(segments[0].startMinutes).toBe(0)
    expect(segments[0].endMinutes).toBe(parseLocalHm('04:45'))
    expect(segments[1].startMinutes).toBe(parseLocalHm('21:30'))
    expect(segments[1].endMinutes).toBe(24 * 60)
  })

  it('returns no darkness segments when no_darkness is true', () => {
    const nights = [night('2025-06-20', { start: '21:30', end: '04:45' }, true)]
    expect(darknessSegmentsForCalendarDay('2025-06-20', nights)).toEqual([])
  })

  it('formats axis labels in 12-hour time', () => {
    expect(formatTimelineAxisLabel(0)).toBe('12 AM')
    expect(formatTimelineAxisLabel(6)).toBe('6 AM')
    expect(formatTimelineAxisLabel(12)).toBe('12 PM')
    expect(formatTimelineAxisLabel(18)).toBe('6 PM')
    expect(formatTimelineAxisLabel(24)).toBe('12 AM')
  })

  it('builds same-day darkness segments without clipping to midnight', () => {
    const nights = [night('2025-06-20', { start: '01:00', end: '05:00' })]
    const segments = darknessSegmentsForCalendarDay('2025-06-20', nights)
    expect(segments).toEqual([segmentFromMinutes(parseLocalHm('01:00'), parseLocalHm('05:00'))])
  })

  it('does not add pre-dawn spillover on the first forecast day without prior window', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const segments = darknessSegmentsForCalendarDay('2025-06-20', nights)

    expect(previousForecastNight('2025-06-20', nights)).toBeUndefined()
    expect(segments).toHaveLength(1)
    expect(segments[0].startMinutes).toBe(parseLocalHm('21:30'))
    expect(segments[0].endMinutes).toBe(24 * 60)
  })

  it('adds pre-dawn spillover on the first forecast day from prior_day_dark_window', () => {
    const nights = [
      night('2025-06-20', { start: '21:30', end: '04:45' }),
      night('2025-06-21', { start: '21:30', end: '04:40' }),
    ]
    const segments = darknessSegmentsForCalendarDay('2025-06-20', nights, {
      firstForecastDate: '2025-06-20',
      priorDayDarkWindow: { start: '21:30', end: '04:45' },
    })

    expect(segments).toHaveLength(2)
    expect(segments[0].startMinutes).toBe(0)
    expect(segments[0].endMinutes).toBe(parseLocalHm('04:45'))
    expect(segments[1].startMinutes).toBe(parseLocalHm('21:30'))
    expect(segments[1].endMinutes).toBe(24 * 60)
  })

  it('adds calendar days without UTC drift', () => {
    expect(addCalendarDays('2025-06-21', -1)).toBe('2025-06-20')
    expect(addCalendarDays('2025-06-20', 1)).toBe('2025-06-21')
  })
})
