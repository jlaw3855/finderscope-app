export type UnitSystem = 'imperial' | 'metric'

export const DEFAULT_UNIT_SYSTEM: UnitSystem = 'imperial'

export const UNIT_SYSTEM_STORAGE_KEY = 'finderscope:unit-system'

const METERS_PER_MILE = 1609.344
const MM_PER_INCH = 25.4

export function fahrenheitToCelsius(fahrenheit: number): number {
  return ((fahrenheit - 32) * 5) / 9
}

export function metersToKm(meters: number): number {
  return meters / 1000
}

export function metersToMiles(meters: number): number {
  return meters / METERS_PER_MILE
}

export function mmToInches(mm: number): number {
  return mm / MM_PER_INCH
}

/** Formats a number with at most maxDecimals places, trimming trailing zeros. */
export function formatDecimal(value: number, maxDecimals: number): string {
  const fixed = value.toFixed(maxDecimals)
  if (!fixed.includes('.')) {
    return fixed
  }
  return fixed.replace(/\.?0+$/, '')
}

export function isUnitSystem(value: string | null): value is UnitSystem {
  return value === 'imperial' || value === 'metric'
}

export function readStoredUnitSystem(): UnitSystem {
  if (typeof window === 'undefined') {
    return DEFAULT_UNIT_SYSTEM
  }

  const stored = window.localStorage.getItem(UNIT_SYSTEM_STORAGE_KEY)
  return isUnitSystem(stored) ? stored : DEFAULT_UNIT_SYSTEM
}
