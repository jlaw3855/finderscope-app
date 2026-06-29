import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  DEFAULT_UNIT_SYSTEM,
  readStoredUnitSystem,
  UNIT_SYSTEM_STORAGE_KEY,
  type UnitSystem,
} from '../lib/unit-system'

interface UnitPreferenceContextValue {
  unitSystem: UnitSystem
  setUnitSystem: (units: UnitSystem) => void
  toggleUnitSystem: () => void
}

const UnitPreferenceContext = createContext<UnitPreferenceContextValue | null>(null)

export function UnitPreferenceProvider({ children }: { children: ReactNode }) {
  const [unitSystem, setUnitSystemState] = useState<UnitSystem>(() => readStoredUnitSystem())

  const setUnitSystem = useCallback((units: UnitSystem) => {
    setUnitSystemState(units)
    window.localStorage.setItem(UNIT_SYSTEM_STORAGE_KEY, units)
  }, [])

  const toggleUnitSystem = useCallback(() => {
    setUnitSystem(unitSystem === DEFAULT_UNIT_SYSTEM ? 'metric' : DEFAULT_UNIT_SYSTEM)
  }, [setUnitSystem, unitSystem])

  const value = useMemo(
    () => ({
      unitSystem,
      setUnitSystem,
      toggleUnitSystem,
    }),
    [setUnitSystem, toggleUnitSystem, unitSystem],
  )

  return (
    <UnitPreferenceContext.Provider value={value}>{children}</UnitPreferenceContext.Provider>
  )
}

export function useUnitPreference(): UnitPreferenceContextValue {
  const context = useContext(UnitPreferenceContext)
  if (!context) {
    throw new Error('useUnitPreference must be used within UnitPreferenceProvider')
  }
  return context
}
