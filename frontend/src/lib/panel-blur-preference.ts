export const DEFAULT_PANEL_BLUR_ENABLED = true

export const PANEL_BLUR_STORAGE_KEY = 'finderscope:panel-blur'

export function readStoredPanelBlur(): boolean {
  if (typeof window === 'undefined') {
    return DEFAULT_PANEL_BLUR_ENABLED
  }

  const stored = window.localStorage.getItem(PANEL_BLUR_STORAGE_KEY)
  if (stored === 'true') {
    return true
  }
  if (stored === 'false') {
    return false
  }
  return DEFAULT_PANEL_BLUR_ENABLED
}
