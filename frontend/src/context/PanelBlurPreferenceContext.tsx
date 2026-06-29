import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  PANEL_BLUR_STORAGE_KEY,
  readStoredPanelBlur,
} from '../lib/panel-blur-preference'

interface PanelBlurPreferenceContextValue {
  panelBlurEnabled: boolean
  setPanelBlurEnabled: (enabled: boolean) => void
}

const PanelBlurPreferenceContext = createContext<PanelBlurPreferenceContextValue | null>(null)

export function PanelBlurPreferenceProvider({ children }: { children: ReactNode }) {
  const [panelBlurEnabled, setPanelBlurEnabledState] = useState<boolean>(() =>
    readStoredPanelBlur(),
  )

  const setPanelBlurEnabled = useCallback((enabled: boolean) => {
    setPanelBlurEnabledState(enabled)
    window.localStorage.setItem(PANEL_BLUR_STORAGE_KEY, String(enabled))
  }, [])

  const value = useMemo(
    () => ({
      panelBlurEnabled,
      setPanelBlurEnabled,
    }),
    [panelBlurEnabled, setPanelBlurEnabled],
  )

  return (
    <PanelBlurPreferenceContext.Provider value={value}>
      {children}
    </PanelBlurPreferenceContext.Provider>
  )
}

export function usePanelBlurPreference(): PanelBlurPreferenceContextValue {
  const context = useContext(PanelBlurPreferenceContext)
  if (!context) {
    throw new Error('usePanelBlurPreference must be used within PanelBlurPreferenceProvider')
  }
  return context
}
