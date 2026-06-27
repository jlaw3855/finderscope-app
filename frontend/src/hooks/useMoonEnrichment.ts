import { useEffect, useMemo, useRef, useState } from 'react'

import { fetchMoonEnrichment } from '../lib/backend-client'
import { moonSampleTimesForForecast } from '../lib/moon-sample-time'
import type { ForecastResponse } from '../types/forecast'
import type { MoonEnrichmentByDate, MoonEnrichmentEntry, MoonEnrichmentStatus } from '../types/moon-enrichment'

const MAX_POLL_ATTEMPTS = 8
const POLL_INTERVAL_MS = 2000

function entriesToMap(entries: MoonEnrichmentEntry[]): MoonEnrichmentByDate {
  return Object.fromEntries(entries.map((entry) => [entry.date, entry]))
}

export function useMoonEnrichment(forecast: ForecastResponse | null) {
  const [byDate, setByDate] = useState<MoonEnrichmentByDate>({})
  const [status, setStatus] = useState<'idle' | 'loading' | MoonEnrichmentStatus>('idle')
  const pollAttempts = useRef(0)

  const requestKey = useMemo(() => {
    if (!forecast || forecast.nights.length === 0) {
      return ''
    }
    const dates = forecast.nights.map((night) => night.date).join(',')
    const sampleTimes = moonSampleTimesForForecast(forecast.nights).join(',')
    return `${dates}|${sampleTimes}`
  }, [forecast])

  useEffect(() => {
    if (!forecast || forecast.nights.length === 0) {
      setByDate({})
      setStatus('idle')
      pollAttempts.current = 0
      return
    }

    let cancelled = false
    pollAttempts.current = 0

    const load = async () => {
      setStatus('loading')
      try {
        const response = await fetchMoonEnrichment(
          forecast.nights.map((night) => night.date),
          forecast.location.timezone,
          moonSampleTimesForForecast(forecast.nights),
        )
        if (cancelled) {
          return
        }

        setByDate((current) => ({ ...current, ...entriesToMap(response.entries) }))
        setStatus(response.status)

        if (
          (response.status === 'pending' || response.status === 'partial') &&
          pollAttempts.current < MAX_POLL_ATTEMPTS
        ) {
          pollAttempts.current += 1
          window.setTimeout(load, POLL_INTERVAL_MS)
        }
      } catch {
        if (!cancelled) {
          setStatus('unavailable')
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [forecast, requestKey])

  return { byDate, status }
}
