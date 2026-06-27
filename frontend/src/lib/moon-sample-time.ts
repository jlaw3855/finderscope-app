import type { NightForecast, TimeWindow } from '../types/forecast'

function parseClockMinutes(time: string): number {
  const [hours, minutes] = time.split(':').map(Number)
  return hours * 60 + minutes
}

function addDays(isoDate: string, days: number): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(Date.UTC(year, month - 1, day))
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

function formatLocalSampleDateTime(isoDate: string, minuteOfDay: number): string {
  const dayOffset = Math.floor(minuteOfDay / (24 * 60))
  const minutes = minuteOfDay % (24 * 60)
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  const datePart = addDays(isoDate, dayOffset)
  return `${datePart}T${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:00`
}

/** Midpoint of astronomical darkness for FreeAstro phase sampling. */
export function darkWindowMidpointIso(nightDate: string, window: TimeWindow): string {
  const startMin = parseClockMinutes(window.start)
  let endMin = parseClockMinutes(window.end)
  if (endMin <= startMin) {
    endMin += 24 * 60
  }
  const midMin = Math.round((startMin + endMin) / 2)
  return formatLocalSampleDateTime(nightDate, midMin)
}

export function moonSampleTimesForForecast(nights: NightForecast[]): string[] {
  return nights.map((night) => {
    if (night.dark_window) {
      return darkWindowMidpointIso(night.date, night.dark_window)
    }
    return `${night.date}T12:00:00`
  })
}
