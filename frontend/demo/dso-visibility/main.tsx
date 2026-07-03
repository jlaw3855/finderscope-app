import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/inter/400.css'
import '@fontsource/inter/600.css'
import '../../src/styles/index.css'
import AppDemoRoot from './AppDemo'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppDemoRoot />
  </StrictMode>,
)
