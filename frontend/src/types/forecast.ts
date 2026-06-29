export interface ForecastRequest {
  address: string
}

export interface LocationInfo {
  label: string
  latitude: number
  longitude: number
  timezone: string
}

export interface TimeWindow {
  start: string
  end: string
}

export interface BestHourWindow {
  start: string
  end: string
  score: number
}

export interface CloudCoverBreakdown {
  total: number | null
  low: number | null
  mid: number | null
  high: number | null
}

export interface PrecipitationBreakdown {
  total_mm: number | null
  max_hourly_mm: number | null
  max_probability: number | null
}

export interface HourlyScore {
  time: string
  at: string
  score: number
  moon_illumination_effective?: number | null
  moon_up?: boolean | null
  moon_altitude?: number | null
  cloud_cover?: number | null
  cloud_cover_low?: number | null
  cloud_cover_mid?: number | null
  cloud_cover_high?: number | null
  visibility?: number | null
  seeing?: number | null
  transparency?: number | null
  precipitation?: number | null
  precipitation_probability?: number | null
  dew_point?: number | null
  temperature?: number | null
}

export interface MeteorShowerHighlight {
  id: string
  name: string
  zhr_nominal: number | null
}

export interface NightForecast {
  date: string
  rating: string
  score: number | null
  moon_phase: string
  moon_illumination: number
  moonrise?: string | null
  moonset?: string | null
  moon_sky_glow_avg?: number | null
  temperature_high?: number | null
  temperature_low?: number | null
  cloud_cover: CloudCoverBreakdown
  precipitation: PrecipitationBreakdown
  dark_window?: TimeWindow | null
  best_hours: BestHourWindow[]
  hourly: HourlyScore[]
  no_darkness: boolean
  meteor_showers: MeteorShowerHighlight[]
  astro_forecast_limited?: boolean
}

export interface ForecastResponse {
  location: LocationInfo
  nights: NightForecast[]
  score_step_minutes?: number
  prior_day_dark_window?: TimeWindow | null
}
