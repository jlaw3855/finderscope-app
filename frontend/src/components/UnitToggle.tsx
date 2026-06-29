import { useUnitPreference } from '../context/UnitPreferenceContext'

export function UnitToggle() {
  const { unitSystem, setUnitSystem } = useUnitPreference()

  return (
    <div className="unit-toggle" role="group" aria-label="Units">
      <span className="unit-toggle-label">Units</span>
      <div className="unit-toggle-options">
        <button
          type="button"
          className={`unit-toggle-option${unitSystem === 'imperial' ? ' active' : ''}`}
          aria-pressed={unitSystem === 'imperial'}
          onClick={() => setUnitSystem('imperial')}
        >
          Imperial
        </button>
        <button
          type="button"
          className={`unit-toggle-option${unitSystem === 'metric' ? ' active' : ''}`}
          aria-pressed={unitSystem === 'metric'}
          onClick={() => setUnitSystem('metric')}
        >
          Metric
        </button>
      </div>
    </div>
  )
}
