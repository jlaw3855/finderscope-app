import type { NightForecast, TimeWindow } from '../types/forecast'

export const PLANET_COLORS: Record<string, string> = {
  Mercury: '#b0b8c8',
  Venus: '#ffd166',
  Mars: '#e85d4c',
  Jupiter: '#c97bff',
  Saturn: '#f4c56a',
  Uranus: '#6ec5d8',
  Neptune: '#4a7cff',
}

export const NAKED_EYE_PLANET_ORDER = [
  'Mercury',
  'Venus',
  'Mars',
  'Jupiter',
  'Saturn',
] as const

export const TELESCOPE_PLANET_ORDER = ['Uranus', 'Neptune'] as const

export const ALL_PLANET_ORDER = [...NAKED_EYE_PLANET_ORDER, ...TELESCOPE_PLANET_ORDER] as const

export const MINUTES_PER_DAY = 24 * 60

export interface TimelineSegment {
  startMinutes: number
  endMinutes: number
  leftPercent: number
  widthPercent: number
}

export function parseLocalHm(value: string): number {
  const [hourPart, minutePart] = value.split(':')
  const hour = Number(hourPart)
  const minute = Number(minutePart)
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) {
    return 0
  }
  return hour * 60 + minute
}

export function minutesToLocalHm(minutes: number): string {
  if (minutes >= MINUTES_PER_DAY) {
    return '24:00'
  }
  const clamped = Math.max(0, Math.min(MINUTES_PER_DAY - 1, Math.round(minutes)))
  const hour = Math.floor(clamped / 60)
  const minute = clamped % 60
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

export function addCalendarDays(dateStr: string, days: number): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  date.setDate(date.getDate() + days)
  const nextYear = date.getFullYear()
  const nextMonth = String(date.getMonth() + 1).padStart(2, '0')
  const nextDay = String(date.getDate()).padStart(2, '0')
  return `${nextYear}-${nextMonth}-${nextDay}`
}

export function segmentFromMinutes(startMinutes: number, endMinutes: number): TimelineSegment {
  const start = Math.max(0, Math.min(MINUTES_PER_DAY, startMinutes))
  const end = Math.max(start, Math.min(MINUTES_PER_DAY, endMinutes))
  return {
    startMinutes: start,
    endMinutes: end,
    leftPercent: (start / MINUTES_PER_DAY) * 100,
    widthPercent: ((end - start) / MINUTES_PER_DAY) * 100,
  }
}

export function windowToSegment(start: string, end: string): TimelineSegment {
  return segmentFromMinutes(parseLocalHm(start), parseLocalHm(end))
}

function crossingMidnight(startMinutes: number, endMinutes: number): boolean {
  return endMinutes <= startMinutes
}

export function previousForecastNight(
  calendarDate: string,
  nights: NightForecast[],
): NightForecast | undefined {
  const previousDate = addCalendarDays(calendarDate, -1)
  return nights.find((entry) => entry.date === previousDate)
}

export interface DarknessSegmentOptions {
  priorDayDarkWindow?: TimeWindow | null
  firstForecastDate?: string
}

export function darknessSegmentsForCalendarDay(
  calendarDate: string,
  nights: NightForecast[],
  options?: DarknessSegmentOptions,
): TimelineSegment[] {
  const segments: TimelineSegment[] = []
  const night = nights.find((entry) => entry.date === calendarDate)
  const previousNight = previousForecastNight(calendarDate, nights)

  if (night?.dark_window && !night.no_darkness) {
    const start = parseLocalHm(night.dark_window.start)
    const end = parseLocalHm(night.dark_window.end)
    if (crossingMidnight(start, end)) {
      segments.push(segmentFromMinutes(start, MINUTES_PER_DAY))
    } else {
      segments.push(segmentFromMinutes(start, end))
    }
  }

  if (previousNight?.dark_window && !previousNight.no_darkness) {
    const start = parseLocalHm(previousNight.dark_window.start)
    const end = parseLocalHm(previousNight.dark_window.end)
    if (crossingMidnight(start, end)) {
      segments.push(segmentFromMinutes(0, end))
    }
  } else if (
    !previousNight &&
    options?.firstForecastDate === calendarDate &&
    options?.priorDayDarkWindow
  ) {
    const start = parseLocalHm(options.priorDayDarkWindow.start)
    const end = parseLocalHm(options.priorDayDarkWindow.end)
    if (crossingMidnight(start, end)) {
      segments.push(segmentFromMinutes(0, end))
    }
  }

  return mergeAdjacentSegments(segments)
}

function mergeAdjacentSegments(segments: TimelineSegment[]): TimelineSegment[] {
  if (segments.length === 0) {
    return []
  }

  const sorted = [...segments].sort((left, right) => left.startMinutes - right.startMinutes)
  const merged: TimelineSegment[] = [sorted[0]]

  for (let index = 1; index < sorted.length; index += 1) {
    const current = sorted[index]
    const last = merged[merged.length - 1]
    if (current.startMinutes <= last.endMinutes) {
      merged[merged.length - 1] = segmentFromMinutes(
        last.startMinutes,
        Math.max(last.endMinutes, current.endMinutes),
      )
      continue
    }
    merged.push(current)
  }

  return merged
}

export function formatTimelineAxisLabel(hour: number): string {
  if (hour === 0 || hour === 24) {
    return '12 AM'
  }
  if (hour === 12) {
    return '12 PM'
  }
  if (hour < 12) {
    return `${hour} AM`
  }
  return `${hour - 12} PM`
}

export const TIMELINE_AXIS_HOURS = [0, 6, 12, 18, 24] as const
