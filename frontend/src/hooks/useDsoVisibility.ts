import { useEffect, useMemo, useState } from 'react'

import { BackendClientError, fetchDsoVisibility } from '../lib/backend-client'
import type { AstronomyResponse } from '../types/astronomy'
import type { DsoVisibilityResponse } from '../types/dso-visibility'
import type { ForecastResponse } from '../types/forecast'

export function useDsoVisibility(
  forecast: ForecastResponse | null,
  _astronomy: AstronomyResponse | null,
  astronomyLoading: boolean,
) {
  const [data, setData] = useState<DsoVisibilityResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const enabled =
    Boolean(forecast && forecast.nights.length > 0) &&
    !astronomyLoading

  const requestKey = useMemo(() => {
    if (!forecast || !enabled) {
      return ''
    }
    const dates = forecast.nights.map((night) => night.date).join(',')
    return `${forecast.location.latitude}|${forecast.location.longitude}|${forecast.location.timezone}|${dates}`
  }, [enabled, forecast])

  useEffect(() => {
    if (!enabled || !forecast) {
      setData(null)
      setError(null)
      setLoading(false)
      return
    }

    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetchDsoVisibility({
          latitude: forecast.location.latitude,
          longitude: forecast.location.longitude,
          timezone: forecast.location.timezone,
          dates: forecast.nights.map((night) => night.date),
        })
        if (!cancelled) {
          setData(response)
        }
      } catch (err) {
        if (!cancelled) {
          setData(null)
          setError(
            err instanceof BackendClientError
              ? err.message
              : 'Unable to load deep sky visibility. Please try again.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [enabled, forecast, requestKey])

  return { data, loading, error }
}
