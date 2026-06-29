export interface ApodResponse {
  title: string
  date: string
  explanation: string
  media_type: 'image' | 'video'
  image_url?: string | null
  video_url?: string | null
  copyright?: string | null
}
