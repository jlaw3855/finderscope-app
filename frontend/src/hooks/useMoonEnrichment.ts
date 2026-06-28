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

function setsEqual(left: Set<string>, right: Set<string>): boolean {
  if (left.size !== right.size) {
    return false
  }
  for (const value of left) {
    if (!right.has(value)) {
      return false
    }
  }
  return true
}

export function useMoonEnrichment(forecast: ForecastResponse | null) {
  const [byDate, setByDate] = useState<MoonEnrichmentByDate>({})
  const [pendingDates, setPendingDates] = useState<Set<string>>(new Set())
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
      setPendingDates(new Set())
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

        const nextPending = new Set(response.pending_dates)
        setByDate((current) => {
          const merged = { ...current, ...entriesToMap(response.entries) }
          const unchanged =
            Object.keys(merged).length === Object.keys(current).length &&
            Object.entries(merged).every(([date, entry]) => current[date] === entry)
          return unchanged ? current : merged
        })
        setPendingDates((current) => (setsEqual(current, nextPending) ? current : nextPending))
        setStatus(response.status)

        if (
          nextPending.size > 0 &&
          (response.status === 'pending' || response.status === 'partial') &&
          pollAttempts.current < MAX_POLL_ATTEMPTS
        ) {
          pollAttempts.current += 1
          window.setTimeout(load, POLL_INTERVAL_MS * pollAttempts.current)
        }
      } catch {
        if (!cancelled) {
          setStatus('unavailable')
          setPendingDates(new Set())
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [forecast, requestKey])

  return { byDate, pendingDates, status }
}
