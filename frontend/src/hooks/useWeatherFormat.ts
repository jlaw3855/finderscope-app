import { useMemo } from 'react'

import { useUnitPreference } from '../context/UnitPreferenceContext'
import { createWeatherFormatters, type WeatherFormatters } from '../lib/weather-format'

export function useWeatherFormat(): WeatherFormatters {
  const { unitSystem } = useUnitPreference()
  return useMemo(() => createWeatherFormatters(unitSystem), [unitSystem])
}
