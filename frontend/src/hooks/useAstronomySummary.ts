import { useEffect, useMemo, useState } from 'react'

import { BackendClientError, fetchAstronomySummary } from '../lib/backend-client'
import type { AstronomyResponse } from '../types/astronomy'
import type { ForecastResponse } from '../types/forecast'

export function useAstronomySummary(forecast: ForecastResponse | null) {
  const [data, setData] = useState<AstronomyResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const requestKey = useMemo(() => {
    if (!forecast || forecast.nights.length === 0) {
      return ''
    }
    const dates = forecast.nights.map((night) => night.date).join(',')
    return `${forecast.location.latitude}|${forecast.location.longitude}|${forecast.location.timezone}|${dates}`
  }, [forecast])

  useEffect(() => {
    if (!forecast || forecast.nights.length === 0) {
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
        const response = await fetchAstronomySummary({
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
              : 'Unable to load astronomy summary. Please try again.',
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
  }, [forecast, requestKey])

  return { data, loading, error }
}
