import {
  MINUTES_PER_DAY,
  parseLocalHm,
  type TimelineSegment,
} from './planet-timeline-layout'

export const DSO_ROW_COLORS = [
  '#7c9cff',
  '#6dd4b0',
  '#f0a06a',
  '#c792ea',
  '#ff7eb6',
  '#82d9ff',
  '#d4c86a',
  '#9ae6b4',
  '#f687b3',
  '#63b3ed',
] as const

export const OBSERVING_AXIS_START_MINUTES = 18 * 60
export const OBSERVING_AXIS_END_MINUTES = 30 * 60
export const OBSERVING_AXIS_SPAN = OBSERVING_AXIS_END_MINUTES - OBSERVING_AXIS_START_MINUTES
const NOON_MINUTES = 12 * 60

export interface ObservingAxisTick {
  extendedMinutes: number
  label: string
}

export const OBSERVING_AXIS_TICKS: ObservingAxisTick[] = [
  { extendedMinutes: 18 * 60, label: '6 PM' },
  { extendedMinutes: 21 * 60, label: '9 PM' },
  { extendedMinutes: 24 * 60, label: '12 AM' },
  { extendedMinutes: 27 * 60, label: '3 AM' },
  { extendedMinutes: 30 * 60, label: '6 AM' },
]

export function toExtendedMinutes(calendarMinutes: number): number {
  if (calendarMinutes >= MINUTES_PER_DAY) {
    return MINUTES_PER_DAY
  }
  if (calendarMinutes < NOON_MINUTES) {
    return calendarMinutes + MINUTES_PER_DAY
  }
  return calendarMinutes
}

export function observingTickLeftPercent(extendedMinutes: number): number {
  return ((extendedMinutes - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100
}

export function observingMinutesToSegment(
  startMinutes: number,
  endMinutes: number,
): TimelineSegment | null {
  const startExt = toExtendedMinutes(startMinutes)
  const endExt = endMinutes >= MINUTES_PER_DAY ? MINUTES_PER_DAY : toExtendedMinutes(endMinutes)
  const clippedStart = Math.max(OBSERVING_AXIS_START_MINUTES, startExt)
  const clippedEnd = Math.min(OBSERVING_AXIS_END_MINUTES, endExt)
  if (clippedEnd <= clippedStart) {
    return null
  }
  return {
    startMinutes: clippedStart,
    endMinutes: clippedEnd,
    leftPercent:
      ((clippedStart - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
    widthPercent: ((clippedEnd - clippedStart) / OBSERVING_AXIS_SPAN) * 100,
  }
}

export function observingWindowToSegment(start: string, end: string): TimelineSegment | null {
  return observingMinutesToSegment(parseLocalHm(start), parseLocalHm(end))
}

export function darknessSegmentsForObservingAxis(
  segments: TimelineSegment[],
): TimelineSegment[] {
  return segments
    .map((segment) => observingMinutesToSegment(segment.startMinutes, segment.endMinutes))
    .filter((segment): segment is TimelineSegment => segment !== null)
}

const DSO_TYPE_LABELS: Record<string, string> = {
  G: 'Galaxy',
  GPair: 'Galaxy pair',
  GTrpl: 'Galaxy triplet',
  GGroup: 'Galaxy group',
  GCl: 'Globular cluster',
  OCl: 'Open cluster',
  'Cl+N': 'Cluster + nebula',
  PN: 'Planetary nebula',
  EmN: 'Emission nebula',
  Neb: 'Nebula',
  RfN: 'Reflection nebula',
  HII: 'H II region',
  SNR: 'Supernova remnant',
}

export function dsoRowColor(index: number): string {
  return DSO_ROW_COLORS[index % DSO_ROW_COLORS.length]
}

export function formatDsoType(objectType: string): string {
  return DSO_TYPE_LABELS[objectType] ?? objectType
}

export function formatDsoLabel(row: { name: string; common_name: string | null }): string {
  if (row.common_name) {
    return `${row.name} · ${row.common_name}`
  }
  return row.name
}

export function formatContrast(value: number): string {
  return value.toFixed(1)
}

export function formatSiteSky(site: {
  bortle: number
  sqm: number
  limiting_magnitude: number
  source: string
}): string {
  const sourceNote = site.source === 'fallback' ? ' · estimated site brightness' : ''
  return `Bortle ${site.bortle} · SQM ${site.sqm.toFixed(1)} · limiting mag ${site.limiting_magnitude.toFixed(1)}${sourceNote}`
}
