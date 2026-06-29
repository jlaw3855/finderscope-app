import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/inter/400.css'
import '@fontsource/inter/600.css'
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
