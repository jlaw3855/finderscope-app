import type { VisibilityWindow } from './astronomy'

export interface SiteSkyConditions {
  bortle: number
  sqm: number
  limiting_magnitude: number
  source: string
}

export interface DsoVisibilityRow {
  id: string
  name: string
  common_name: string | null
  messier: number | null
  object_type: string
  visible: boolean
  windows_astronomical: VisibilityWindow[]
  peak_altitude_deg: number | null
  peak_at: string | null
  magnitude: number | null
  contrast: number
  visibility_score: number
}

export interface DsoDayVisibility {
  date: string
  objects: DsoVisibilityRow[]
}

export interface DsoVisibilityRequest {
  latitude: number
  longitude: number
  timezone: string
  dates: string[]
}

export interface DsoVisibilityResponse {
  site_sky: SiteSkyConditions
  dso_visibility: DsoDayVisibility[]
}
