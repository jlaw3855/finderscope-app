import { useEffect, useState } from 'react'

import { BackendClientError, fetchApod } from '../lib/backend-client'
import type { ApodResponse } from '../types/apod'

export function useApod() {
  const [data, setData] = useState<ApodResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetchApod()
        if (!cancelled) {
          setData(response)
        }
      } catch (err) {
        if (!cancelled) {
          setData(null)
          setError(
            err instanceof BackendClientError
              ? err.message
              : 'Unable to load Astronomy Picture of the Day.',
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
  }, [])

  return { data, loading, error }
}
