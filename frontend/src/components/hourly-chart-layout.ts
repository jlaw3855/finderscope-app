/** Shared layout helpers for the hourly score grid and temperature chart. */

export const HOURLY_COLUMN_WIDTH_HOUR = 99
export const HOURLY_COLUMN_WIDTH_HALF_HOUR = 56
export const HOURLY_COLUMN_GAP_HOUR = 12
export const HOURLY_COLUMN_GAP_HALF_HOUR = 5.6

export function getHourlyColumnWidth(stepMinutes: number): number {
  return stepMinutes === 30 ? HOURLY_COLUMN_WIDTH_HALF_HOUR : HOURLY_COLUMN_WIDTH_HOUR
}

export function getHourlyColumnGap(stepMinutes: number): number {
  return stepMinutes === 30 ? HOURLY_COLUMN_GAP_HALF_HOUR : HOURLY_COLUMN_GAP_HOUR
}

/** Total scroll width for N columns (px). */
export function getHourlyGridWidth(columnCount: number, stepMinutes: number): number {
  if (columnCount <= 0) {
    return 0
  }
  const colWidth = getHourlyColumnWidth(stepMinutes)
  const gap = getHourlyColumnGap(stepMinutes)
  return columnCount * colWidth + (columnCount - 1) * gap
}

/** X center of column index in the shared grid (px). */
export function getHourlyColumnCenterX(index: number, stepMinutes: number): number {
  const colWidth = getHourlyColumnWidth(stepMinutes)
  const gap = getHourlyColumnGap(stepMinutes)
  return index * (colWidth + gap) + colWidth / 2
}

export function shouldShowTimeLabel(index: number, total: number, stepMinutes: number): boolean {
  if (stepMinutes !== 30) {
    return true
  }
  if (index === total - 1) {
    return true
  }
  return index % 2 === 0
}

export interface TemperatureScale {
  minValue: number
  maxValue: number
  valueRange: number
}

const TEMP_SCALE_PADDING_F = 3
const TEMP_SCALE_MIN_RANGE_F = 8

export function buildTemperatureScale(
  dewPoints: number[],
  temperatures: number[],
): TemperatureScale | null {
  const allValues = [...dewPoints, ...temperatures]
  if (allValues.length === 0) {
    return null
  }

  const rawMin = Math.min(...allValues)
  const rawMax = Math.max(...allValues)
  let minValue = Math.floor(rawMin - TEMP_SCALE_PADDING_F)
  let maxValue = Math.ceil(rawMax + TEMP_SCALE_PADDING_F)

  if (maxValue - minValue < TEMP_SCALE_MIN_RANGE_F) {
    const center = (rawMin + rawMax) / 2
    minValue = Math.floor(center - TEMP_SCALE_MIN_RANGE_F / 2)
    maxValue = Math.ceil(center + TEMP_SCALE_MIN_RANGE_F / 2)
  }

  return {
    minValue,
    maxValue,
    valueRange: Math.max(maxValue - minValue, 1),
  }
}

export function valueToChartY(
  value: number,
  scale: TemperatureScale,
  plotTop: number,
  plotHeight: number,
): number {
  return plotTop + plotHeight - ((value - scale.minValue) / scale.valueRange) * plotHeight
}

export function buildTemperatureTicks(scale: TemperatureScale, tickCount = 5): number[] {
  const { minValue, valueRange } = scale
  if (tickCount <= 1 || valueRange === 0) {
    return [minValue]
  }

  const ticks: number[] = []
  for (let index = 0; index < tickCount; index += 1) {
    const fraction = index / (tickCount - 1)
    ticks.push(minValue + fraction * valueRange)
  }
  return ticks
}
