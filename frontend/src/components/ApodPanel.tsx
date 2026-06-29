import { useApod } from '../hooks/useApod'
import { formatApodExplanation } from '../lib/apod-format'

function youtubeEmbedUrl(videoUrl: string): string | null {
  try {
    const parsed = new URL(videoUrl)
    if (parsed.hostname.includes('youtube.com')) {
      const videoId = parsed.searchParams.get('v')
      return videoId ? `https://www.youtube.com/embed/${videoId}` : null
    }
    if (parsed.hostname === 'youtu.be') {
      const videoId = parsed.pathname.replace('/', '')
      return videoId ? `https://www.youtube.com/embed/${videoId}` : null
    }
  } catch {
    return null
  }
  return null
}

export function ApodPanel() {
  const { data, loading, error } = useApod()

  if (loading) {
    return (
      <section className="panel apod-panel" data-testid="apod-panel">
        <p className="muted">Loading Astronomy Picture of the Day…</p>
      </section>
    )
  }

  if (error || !data) {
    return (
      <section className="panel apod-panel" data-testid="apod-panel">
        <p className="muted">{error ?? 'Astronomy Picture of the Day is unavailable.'}</p>
      </section>
    )
  }

  const credit = data.copyright?.trim() || 'Public domain (NASA)'
  const embedUrl = data.media_type === 'video' && data.video_url ? youtubeEmbedUrl(data.video_url) : null

  return (
    <section className="panel apod-panel" data-testid="apod-panel">
      <header className="apod-header">
        <p className="apod-kicker muted">Astronomy Picture of the Day</p>
        <h2 className="apod-title">{data.title}</h2>
      </header>

      <div className="apod-media">
        {data.media_type === 'image' && data.image_url ? (
          <img src={data.image_url} alt={data.title} className="apod-image" loading="lazy" />
        ) : embedUrl ? (
          <iframe
            src={embedUrl}
            title={data.title}
            className="apod-video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        ) : data.video_url ? (
          <a href={data.video_url} className="apod-video-link" target="_blank" rel="noreferrer">
            Watch today&apos;s APOD video
          </a>
        ) : null}
      </div>

      <p className="apod-credit">
        <strong>Credit &amp; copyright:</strong> {credit}
      </p>

      <p className="apod-explanation">{formatApodExplanation(data.explanation)}</p>

      <footer className="apod-footer muted">
        Image and metadata from NASA&apos;s Astronomy Picture of the Day via the{' '}
        <a href="https://api.nasa.gov/" target="_blank" rel="noreferrer">
          NASA Open APIs
        </a>
        .
      </footer>
    </section>
  )
}
