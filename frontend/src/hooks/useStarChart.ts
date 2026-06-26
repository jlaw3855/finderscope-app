import { useCallback, useState } from 'react'

import { BackendClientError, fetchStarChart } from '../lib/backend-client'
import type { StarChartRequest, StarChartResponse } from '../types/star-chart'

export function useStarChart() {
  const [data, setData] = useState<StarChartResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = useCallback(async (request: StarChartRequest) => {
    setLoading(true)
    setError(null)

    try {
      const result = await fetchStarChart(request)
      setData(result)
      return result
    } catch (err) {
      const message =
        err instanceof BackendClientError
          ? err.message
          : 'Unable to generate star chart. Please try again.'
      setError(message)
      setData(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, generate }
}
