import type { ReactNode } from 'react'

import { UnitPreferenceProvider } from '../context/UnitPreferenceContext'

export function withUnitProvider(ui: ReactNode) {
  return <UnitPreferenceProvider>{ui}</UnitPreferenceProvider>
}
