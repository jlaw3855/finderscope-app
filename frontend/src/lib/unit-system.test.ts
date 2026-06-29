import { describe, expect, it } from 'vitest'

import {
  fahrenheitToCelsius,
  formatDecimal,
  metersToKm,
  metersToMiles,
  mmToInches,
} from './unit-system'

describe('fahrenheitToCelsius', () => {
  it('converts freezing point', () => {
    expect(fahrenheitToCelsius(32)).toBeCloseTo(0)
  })

  it('converts room temperature', () => {
    expect(fahrenheitToCelsius(72)).toBeCloseTo(22.222, 2)
  })
})

describe('metersToKm', () => {
  it('converts meters to kilometers', () => {
    expect(metersToKm(5500)).toBe(5.5)
  })
})

describe('metersToMiles', () => {
  it('converts meters to miles', () => {
    expect(metersToMiles(1609.344)).toBeCloseTo(1)
  })
})

describe('mmToInches', () => {
  it('converts millimeters to inches', () => {
    expect(mmToInches(25.4)).toBeCloseTo(1)
  })
})

describe('formatDecimal', () => {
  it('caps decimal places', () => {
    expect(formatDecimal(3.456, 1)).toBe('3.5')
  })

  it('trims trailing zeros', () => {
    expect(formatDecimal(3.5, 2)).toBe('3.5')
  })

  it('never exceeds two decimal places', () => {
    expect(formatDecimal(1.234, 2)).toBe('1.23')
  })
})
