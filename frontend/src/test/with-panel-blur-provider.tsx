import type { ReactNode } from 'react'

import { PanelBlurPreferenceProvider } from '../context/PanelBlurPreferenceContext'

export function withPanelBlurProvider(ui: ReactNode) {
  return <PanelBlurPreferenceProvider>{ui}</PanelBlurPreferenceProvider>
}
