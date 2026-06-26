export type StarChartViewType = 'all-sky' | 'constellation'

export interface StarChartRequest {
  latitude: number
  longitude: number
  date: string
  time: string
  view_type: StarChartViewType
  constellation?: string | null
}

export interface StarChartResponse {
  image_url: string
  view_type: string
}
