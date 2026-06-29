import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'

import type { ApodResponse } from '../types/apod'
import { ApodPanel } from './ApodPanel'

const imageApod: ApodResponse = {
  title: 'Starlink over Orion',
  date: '2025-06-20',
  explanation: 'Sample APOD explanation for testing.',
  media_type: 'image',
  image_url: 'https://example.com/apod.jpg',
  copyright: 'Robert Gendler',
}

const videoApod: ApodResponse = {
  title: 'Sample Video APOD',
  date: '2025-06-21',
  explanation: 'Video explanation for testing.',
  media_type: 'video',
  video_url: 'https://www.youtube.com/watch?v=abc123',
}

vi.mock('../hooks/useApod', () => ({
  useApod: vi.fn(),
}))

import { useApod } from '../hooks/useApod'

const mockedUseApod = vi.mocked(useApod)

describe('ApodPanel', () => {
  it('renders image APOD metadata and attribution footer', () => {
    mockedUseApod.mockReturnValue({ data: imageApod, loading: false, error: null })

    const html = renderToStaticMarkup(<ApodPanel />)

    expect(html).toContain('Astronomy Picture of the Day')
    expect(html).toContain('Starlink over Orion')
    expect(html).toContain('Credit &amp; copyright:')
    expect(html).toContain('Robert Gendler')
    expect(html).toContain('Sample APOD explanation for testing.')
    expect(html).toContain('NASA Open APIs')
    expect(html).toContain('apod-image')
  })

  it('uses public domain credit when copyright is missing', () => {
    mockedUseApod.mockReturnValue({
      data: { ...imageApod, copyright: null },
      loading: false,
      error: null,
    })

    const html = renderToStaticMarkup(<ApodPanel />)
    expect(html).toContain('Public domain (NASA)')
  })

  it('renders a video embed for YouTube APOD entries', () => {
    mockedUseApod.mockReturnValue({ data: videoApod, loading: false, error: null })

    const html = renderToStaticMarkup(<ApodPanel />)
    expect(html).toContain('apod-video')
    expect(html).toContain('https://www.youtube.com/embed/abc123')
  })

  it('omits the Sky Surprise footer from the explanation', () => {
    mockedUseApod.mockReturnValue({
      data: {
        ...imageApod,
        explanation:
          'Main caption text. Sky Surprise: What picture did APOD feature on your birthday? (after 1995)',
      },
      loading: false,
      error: null,
    })

    const html = renderToStaticMarkup(<ApodPanel />)
    expect(html).toContain('Main caption text.')
    expect(html).not.toContain('Sky Surprise')
  })
})
