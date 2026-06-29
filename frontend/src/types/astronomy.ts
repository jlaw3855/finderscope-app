export type AstronomyEventCategory =
  | 'lunar_eclipse'
  | 'solar_eclipse'
  | 'transit'
  | 'conjunction'
  | 'opposition'
  | 'meteor_shower'

export interface SkySourceEnrichment {
  query: string
  short_name: string | null
  types: string[]
  interest: number | null
  names: string[]
  model: string | null
}

export interface AstronomyEvent {
  id: string
  category: AstronomyEventCategory
  title: string
  start_at: string
  peak_at: string | null
  end_at: string | null
  description: string
  visible_locally: boolean
  subjects: SkySourceEnrichment[]
}

export interface VisibilityWindow {
  start: string
  end: string
}

export interface PlanetVisibilityRow {
  body: string
  visible: boolean
  windows_civil: VisibilityWindow[]
  windows_astronomical: VisibilityWindow[]
  peak_altitude_deg: number | null
  peak_at: string | null
  magnitude: number | null
}

export interface PlanetDayVisibility {
  date: string
  planets: PlanetVisibilityRow[]
}

export interface AstronomyRequest {
  latitude: number
  longitude: number
  timezone: string
  dates: string[]
}

export interface AstronomyResponse {
  events: AstronomyEvent[]
  planet_visibility: PlanetDayVisibility[]
}
