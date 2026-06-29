import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App.tsx'
import { UnitPreferenceProvider } from './context/UnitPreferenceContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UnitPreferenceProvider>
      <App />
    </UnitPreferenceProvider>
  </StrictMode>,
)
