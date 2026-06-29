import { usePanelBlurPreference } from '../context/PanelBlurPreferenceContext'

export function PanelBlurToggle() {
  const { panelBlurEnabled, setPanelBlurEnabled } = usePanelBlurPreference()

  return (
    <div className="panel-blur-floating">
      <button
        type="button"
        className="unit-toggle"
        aria-label="Panel blur"
        aria-pressed={panelBlurEnabled}
        onClick={() => setPanelBlurEnabled(!panelBlurEnabled)}
      >
        <span className="unit-toggle-label">Panel opacity</span>
        <div className="unit-toggle-options">
          <span className={`unit-toggle-option${panelBlurEnabled ? ' active' : ''}`}>On</span>
          <span className={`unit-toggle-option${!panelBlurEnabled ? ' active' : ''}`}>Off</span>
        </div>
      </button>
    </div>
  )
}
