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

export function segmentFromExtendedBounds(startExt: number, endExt: number): TimelineSegment {
  const clippedStart = Math.max(OBSERVING_AXIS_START_MINUTES, startExt)
  const clippedEnd = Math.min(OBSERVING_AXIS_END_MINUTES, endExt)
  return {
    startMinutes: clippedStart,
    endMinutes: clippedEnd,
    leftPercent:
      ((clippedStart - OBSERVING_AXIS_START_MINUTES) / OBSERVING_AXIS_SPAN) * 100,
    widthPercent: ((clippedEnd - clippedStart) / OBSERVING_AXIS_SPAN) * 100,
  }
}

export function mergeObservingTimelineSegments(segments: TimelineSegment[]): TimelineSegment[] {
  if (segments.length === 0) {
    return []
  }

  const sorted = [...segments].sort((left, right) => left.startMinutes - right.startMinutes)
  const merged: TimelineSegment[] = []
  let current = { ...sorted[0] }

  for (let index = 1; index < sorted.length; index += 1) {
    const next = sorted[index]
    if (next.startMinutes - current.endMinutes <= 1) {
      current = segmentFromExtendedBounds(
        current.startMinutes,
        Math.max(current.endMinutes, next.endMinutes),
      )
    } else {
      merged.push(current)
      current = { ...next }
    }
  }

  merged.push(current)
  return merged
}

function observingSegmentSetsEquivalent(
  left: TimelineSegment[],
  right: TimelineSegment[],
): boolean {
  const mergedLeft = mergeObservingTimelineSegments(left)
  const mergedRight = mergeObservingTimelineSegments(right)
  if (mergedLeft.length === 0 || mergedRight.length === 0) {
    return false
  }
  if (mergedLeft.length !== mergedRight.length) {
    return false
  }
  return mergedLeft.every((segment, index) => {
    const other = mergedRight[index]
    return (
      Math.abs(segment.startMinutes - other.startMinutes) <= 1 &&
      Math.abs(segment.endMinutes - other.endMinutes) <= 1
    )
  })
}

export function astroUnionSegmentsFromObjects(
  objects: { windows_astronomical: ObservingTimeWindow[] }[],
): TimelineSegment[] {
  const segments = objects.flatMap((object) =>
    mergeObservingWindows(object.windows_astronomical)
      .map((window) => observingWindowToSegment(window.start, window.end))
      .filter((segment): segment is TimelineSegment => segment !== null),
  )
  return mergeObservingTimelineSegments(segments)
}

export function forecastAndAstroDarknessFullyOverlap(
  objects: { windows_astronomical: ObservingTimeWindow[] }[],
  calendarDarknessSegments: TimelineSegment[],
): boolean {
  const forecast = mergeObservingTimelineSegments(
    darknessSegmentsForObservingAxis(calendarDarknessSegments),
  )
  const astro = astroUnionSegmentsFromObjects(objects)
  return observingSegmentSetsEquivalent(forecast, astro)
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

export function formatDsoLabel(row: {
  name: string
  common_name: string | null
  messier?: number | null
}): string {
  const catalogLabel =
    row.messier != null ? `M${row.messier}` : row.name
  if (row.common_name) {
    return `${catalogLabel} · ${row.common_name}`
  }
  return catalogLabel
}

export function formatDsoShortLabel(row: {
  name: string
  messier?: number | null
}): string {
  if (row.messier != null) {
    return `M${row.messier}`
  }
  return row.name
}

export interface ObservingTimeWindow {
  start: string
  end: string
}

function windowStartExtended(start: string): number {
  return toExtendedMinutes(parseLocalHm(start))
}

function windowEndExtended(end: string): number {
  const endMinutes = parseLocalHm(end)
  return endMinutes >= MINUTES_PER_DAY ? MINUTES_PER_DAY : toExtendedMinutes(endMinutes)
}

export function mergeObservingWindows(windows: ObservingTimeWindow[]): ObservingTimeWindow[] {
  if (windows.length === 0) {
    return []
  }

  const sorted = [...windows].sort(
    (left, right) => windowStartExtended(left.start) - windowStartExtended(right.start),
  )
  const merged: ObservingTimeWindow[] = []
  let current = { ...sorted[0] }

  for (let index = 1; index < sorted.length; index += 1) {
    const next = sorted[index]
    const gapMinutes = windowStartExtended(next.start) - windowEndExtended(current.end)
    if (gapMinutes <= 1) {
      current = { start: current.start, end: next.end }
    } else {
      merged.push(current)
      current = { ...next }
    }
  }

  merged.push(current)
  return merged
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
