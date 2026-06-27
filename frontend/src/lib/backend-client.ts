import type { AstronomyRequest, AstronomyResponse } from '../types/astronomy'
import type { ForecastRequest, ForecastResponse } from '../types/forecast'
import type { MoonEnrichmentResponse } from '../types/moon-enrichment'

class BackendClientError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'BackendClientError'
    this.status = status
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') {
      return data.detail
    }
    if (Array.isArray(data.detail)) {
      return data.detail.map((item: { msg?: string }) => item.msg).join(', ')
    }
    return response.statusText || 'Request failed'
  } catch {
    return response.statusText || 'Request failed'
  }
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const message = await parseError(response)
    throw new BackendClientError(message, response.status)
  }

  return response.json() as Promise<T>
}

export async function fetchForecast(request: ForecastRequest): Promise<ForecastResponse> {
  return postJson<ForecastResponse>('/api/forecast', request)
}

export async function fetchAstronomySummary(request: AstronomyRequest): Promise<AstronomyResponse> {
  return postJson<AstronomyResponse>('/api/astronomy', request)
}

export async function fetchMoonEnrichment(
  dates: string[],
  timezone: string,
  sampleTimes?: string[],
): Promise<MoonEnrichmentResponse> {
  const params = new URLSearchParams({
    dates: dates.join(','),
    timezone,
  })
  if (sampleTimes && sampleTimes.length > 0) {
    params.set('sample_times', sampleTimes.join(','))
  }
  const response = await fetch(`/api/moon/enrichment?${params.toString()}`)

  if (!response.ok) {
    const message = await parseError(response)
    throw new BackendClientError(message, response.status)
  }

  return response.json() as Promise<MoonEnrichmentResponse>
}

export { BackendClientError }
