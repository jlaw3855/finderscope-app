import { describe, expect, it } from 'vitest'

import {
  buildTemperatureScale,
  buildTemperatureTicks,
  getHourlyColumnCenterX,
  getHourlyGridWidth,
  shouldShowTimeLabel,
  valueToChartY,
} from './hourly-chart-layout'

describe('hourly-chart-layout', () => {
  it('computes grid width from column count and step', () => {
    expect(getHourlyGridWidth(3, 60)).toBe(3 * 99 + 2 * 12)
    expect(getHourlyGridWidth(4, 30)).toBe(4 * 56 + 3 * 5.6)
  })

  it('places column centers for alignment', () => {
    expect(getHourlyColumnCenterX(0, 60)).toBe(99 / 2)
    expect(getHourlyColumnCenterX(1, 60)).toBe(99 + 12 + 99 / 2)
  })

  it('sparse time labels for half-hour steps', () => {
    expect(shouldShowTimeLabel(0, 5, 30)).toBe(true)
    expect(shouldShowTimeLabel(1, 5, 30)).toBe(false)
    expect(shouldShowTimeLabel(4, 5, 30)).toBe(true)
    expect(shouldShowTimeLabel(1, 5, 60)).toBe(true)
  })

  it('builds temperature scale from dew and air values', () => {
    const scale = buildTemperatureScale([42, 44], [50, 52])
    expect(scale).not.toBeNull()
    expect(scale!.minValue).toBeLessThanOrEqual(39)
    expect(scale!.maxValue).toBeGreaterThanOrEqual(55)
    expect(scale!.valueRange).toBeGreaterThanOrEqual(8)
  })

  it('enforces minimum temperature range for close values', () => {
    const scale = buildTemperatureScale([50, 50.5], [51, 51.5])
    expect(scale).not.toBeNull()
    expect(scale!.valueRange).toBeGreaterThanOrEqual(8)
  })

  it('maps values to chart coordinates', () => {
    const scale = { minValue: 40, maxValue: 50, valueRange: 10 }
    expect(valueToChartY(40, scale, 10, 100)).toBe(110)
    expect(valueToChartY(50, scale, 10, 100)).toBe(10)
  })

  it('builds evenly spaced temperature ticks', () => {
    const scale = buildTemperatureScale([40], [50])!
    const ticks = buildTemperatureTicks(scale, 3)
    expect(ticks).toHaveLength(3)
    expect(ticks[0]).toBe(scale.minValue)
    expect(ticks[2]).toBe(scale.maxValue)
  })
})
