import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'

import { PanelBlurToggle } from './PanelBlurToggle'
import { PANEL_BLUR_STORAGE_KEY } from '../lib/panel-blur-preference'
import { withPanelBlurProvider } from '../test/with-panel-blur-provider'

describe('PanelBlurToggle', () => {
  it('renders on and off options with on active by default', () => {
    const html = renderToStaticMarkup(withPanelBlurProvider(<PanelBlurToggle />))
    expect(html).toContain('Panel opacity')
    expect(html).toContain('panel-blur-floating')
    expect(html).toContain('>On</span>')
    expect(html).toContain('>Off</span>')
    expect(html).toContain('aria-pressed="true"')
  })

  it('renders off active when localStorage preference is false', () => {
    vi.stubGlobal('window', {
      localStorage: {
        getItem: (key: string) => (key === PANEL_BLUR_STORAGE_KEY ? 'false' : null),
        setItem: vi.fn(),
      },
    })

    const html = renderToStaticMarkup(withPanelBlurProvider(<PanelBlurToggle />))
    expect(html).toContain('>Off</span>')
    expect(html).toContain('aria-pressed="false"')

    vi.unstubAllGlobals()
  })
})
