import { useCallback, useState } from 'react'

import { BackendClientError, fetchForecast } from '../lib/backend-client'
import type { ForecastResponse } from '../types/forecast'

export function useForecast() {
  const [data, setData] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (address: string) => {
    setLoading(true)
    setError(null)

    try {
      const result = await fetchForecast({ address })
      setData(result)
      return result
    } catch (err) {
      const message =
        err instanceof BackendClientError
          ? err.message
          : 'Unable to fetch forecast. Please try again.'
      setError(message)
      setData(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, search }
}
