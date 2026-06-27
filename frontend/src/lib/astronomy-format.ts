import type { AstronomyEvent, AstronomyEventCategory } from '../types/astronomy'

const CATEGORY_LABELS: Record<AstronomyEventCategory, string> = {
  lunar_eclipse: 'Lunar eclipse',
  solar_eclipse: 'Solar eclipse',
  transit: 'Transit',
  conjunction: 'Conjunction',
  opposition: 'Opposition',
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

export function formatVisibilityWindows(windows: { start: string; end: string }[]): string {
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

export function eventCategoryClass(category: AstronomyEventCategory): string {
  return `astronomy-event--${category.replace('_', '-')}`
}

export function sortEventsByStart(events: AstronomyEvent[]): AstronomyEvent[] {
  return [...events].sort(
    (left, right) => new Date(left.start_at).getTime() - new Date(right.start_at).getTime(),
  )
}

export function altitudeBarPercent(altitude: number | null): number {
  if (altitude == null) {
    return 0
  }
  return Math.max(0, Math.min(100, (altitude / 90) * 100))
}
