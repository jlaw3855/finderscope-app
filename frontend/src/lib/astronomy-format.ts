import type { AstronomyEvent, AstronomyEventCategory, SkySourceEnrichment } from '../types/astronomy'

const CATEGORY_LABELS: Record<AstronomyEventCategory, string> = {
  lunar_eclipse: 'Lunar eclipse',
  solar_eclipse: 'Solar eclipse',
  transit: 'Transit',
  conjunction: 'Conjunction',
  opposition: 'Opposition',
  meteor_shower: 'Meteor shower',
}

export function formatEventCategory(category: AstronomyEventCategory): string {
  return CATEGORY_LABELS[category]
}

export function formatEventDate(iso: string, timezone: string): string {
  const date = new Date(iso)
  return date.toLocaleString(undefined, {
    timeZone: timezone,
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatNightColumnDate(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00`)
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

export function formatForecastNightHeading(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00`)
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

export function formatVisibilityWindows(
  civil: { start: string; end: string }[],
  astronomical: { start: string; end: string }[],
): string {
  const parts: string[] = []
  if (civil.length > 0) {
    parts.push(
      `civil: ${civil.map((window) => `${window.start} – ${window.end}`).join('; ')}`,
    )
  }
  if (astronomical.length > 0) {
    parts.push(
      `astro: ${astronomical.map((window) => `${window.start} – ${window.end}`).join('; ')}`,
    )
  }
  return parts.length > 0 ? parts.join(' · ') : '—'
}

export function formatAstroWindows(windows: { start: string; end: string }[]): string {
  if (windows.length === 0) {
    return '—'
  }
  return windows.map((window) => `${window.start} – ${window.end}`).join('; ')
}

export function formatMagnitude(value: number | null): string {
  if (value == null) {
    return '—'
  }
  return value.toFixed(1)
}

export function formatPeakAltitude(value: number | null): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value)}°`
}

export function formatAlmanacTime(
  value: string | null,
  alwaysUp: boolean,
  alwaysDown: boolean,
  kind: 'rise' | 'set' | 'transit' = 'transit',
): string {
  if (value) {
    return value
  }
  if (alwaysUp) {
    return kind === 'set' ? '—' : 'Always up'
  }
  if (alwaysDown) {
    return kind === 'rise' ? '—' : 'Always down'
  }
  return '—'
}

export function formatMoonOffsetAxis(value: number, axis: 'east' | 'north'): string {
  const abs = Math.abs(value)
  if (abs < 0.05) {
    return axis === 'east' ? 'on disk' : 'on disk'
  }
  const direction =
    axis === 'east'
      ? value >= 0
        ? 'E'
        : 'W'
      : value >= 0
        ? 'N'
        : 'S'
  return `${abs.toFixed(1)}′ ${direction}`
}

export function formatJupiterMoons(detail: {
  sampled_at: string
  moons: { name: string; east_arcmin: number; north_arcmin: number }[]
}): string {
  const moonLabels = detail.moons.map((moon) => {
    const east = formatMoonOffsetAxis(moon.east_arcmin, 'east')
    const north = formatMoonOffsetAxis(moon.north_arcmin, 'north')
    if (east === 'on disk' && north === 'on disk') {
      return `${moon.name} on disk`
    }
    if (east === 'on disk') {
      return `${moon.name} ${north}`
    }
    if (north === 'on disk') {
      return `${moon.name} ${east}`
    }
    return `${moon.name} ${east} ${north}`
  })
  return `Moons at ${detail.sampled_at} · ${moonLabels.join(' · ')}`
}

export function formatSaturnRings(tilt: number, note: string | null): string {
  const noteText = note ? ` · ${note.toLowerCase()}` : ''
  return `Ring tilt ${tilt.toFixed(1)}°${noteText}`
}

export function eventCategoryClass(category: AstronomyEventCategory): string {
  return `astronomy-event--${category.replace(/_/g, '-')}`
}

export function formatSubjectTypes(subject: SkySourceEnrichment): string {
  if (subject.types.length === 0) {
    return subject.short_name ?? subject.query
  }
  return subject.types.join(', ')
}

export function formatSubjectInterest(interest: number | null): string | null {
  if (interest == null) {
    return null
  }
  return `Interest ${interest.toFixed(1)}`
}

export function formatSubjectAliases(subject: SkySourceEnrichment): string | null {
  if (subject.names.length <= 1) {
    return null
  }
  const aliases = subject.names.filter((name) => name !== subject.short_name).slice(0, 3)
  if (aliases.length === 0) {
    return null
  }
  return aliases.join(' · ')
}

export function sortEventsByStart(events: AstronomyEvent[]): AstronomyEvent[] {
  return [...events].sort(
    (left, right) => new Date(left.start_at).getTime() - new Date(right.start_at).getTime(),
  )
}
