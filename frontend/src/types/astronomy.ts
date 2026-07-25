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
  jupiter_moons?: JupiterMoonsDetail | null
  saturn_ring_tilt_deg?: number | null
  saturn_ring_note?: string | null
}

export interface JupiterMoonOffset {
  name: 'Io' | 'Europa' | 'Ganymede' | 'Callisto'
  east_arcmin: number
  north_arcmin: number
}

export interface JupiterMoonsDetail {
  sampled_at: string
  moons: JupiterMoonOffset[]
}

export interface CelestialAlmanacRow {
  body: string
  rise_at: string | null
  transit_at: string | null
  set_at: string | null
  transit_altitude_deg: number | null
  always_up: boolean
  always_down: boolean
}

export interface CelestialDayAlmanac {
  date: string
  rows: CelestialAlmanacRow[]
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
  almanac: CelestialDayAlmanac[]
}
