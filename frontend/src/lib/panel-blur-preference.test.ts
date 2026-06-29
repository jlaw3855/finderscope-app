import { describe, expect, it, vi } from 'vitest'

import {
  DEFAULT_PANEL_BLUR_ENABLED,
  PANEL_BLUR_STORAGE_KEY,
  readStoredPanelBlur,
} from './panel-blur-preference'

describe('readStoredPanelBlur', () => {
  it('returns default when window is unavailable', () => {
    expect(readStoredPanelBlur()).toBe(DEFAULT_PANEL_BLUR_ENABLED)
  })

  it('reads true from localStorage', () => {
    vi.stubGlobal('window', {
      localStorage: {
        getItem: (key: string) => (key === PANEL_BLUR_STORAGE_KEY ? 'true' : null),
      },
    })
    expect(readStoredPanelBlur()).toBe(true)
    vi.unstubAllGlobals()
  })

  it('reads false from localStorage', () => {
    vi.stubGlobal('window', {
      localStorage: {
        getItem: (key: string) => (key === PANEL_BLUR_STORAGE_KEY ? 'false' : null),
      },
    })
    expect(readStoredPanelBlur()).toBe(false)
    vi.unstubAllGlobals()
  })

  it('falls back to default for invalid stored values', () => {
    vi.stubGlobal('window', {
      localStorage: {
        getItem: (key: string) => (key === PANEL_BLUR_STORAGE_KEY ? 'yes' : null),
      },
    })
    expect(readStoredPanelBlur()).toBe(DEFAULT_PANEL_BLUR_ENABLED)
    vi.unstubAllGlobals()
  })
})
