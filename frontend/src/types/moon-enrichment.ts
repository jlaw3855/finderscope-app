export type MoonEnrichmentStatus = 'complete' | 'partial' | 'pending' | 'unavailable'

export interface MoonEnrichmentEntry {
  date: string
  phase_name: string
  illumination_pct: number
  age_days?: number | null
  is_waxing?: boolean | null
  special_labels: string[]
  visual_url?: string | null
}

export interface MoonEnrichmentResponse {
  entries: MoonEnrichmentEntry[]
  status: MoonEnrichmentStatus
  cached_count: number
  pending_dates: string[]
}

export interface MoonEnrichmentByDate {
  [date: string]: MoonEnrichmentEntry
}
