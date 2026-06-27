import { useState } from 'react'

import { AddressSearch } from './components/AddressSearch'
import { AstronomyEventsPanel } from './components/AstronomyEventsPanel'
import { ErrorBanner } from './components/ErrorBanner'
import { HourlyScoreChart } from './components/HourlyScoreChart'
import { NightForecastCard } from './components/NightForecastCard'
import { useAstronomySummary } from './hooks/useAstronomySummary'
import { useForecast } from './hooks/useForecast'
import { useMoonEnrichment } from './hooks/useMoonEnrichment'

function App() {
  const { data: forecast, loading: forecastLoading, error: forecastError, search } = useForecast()
  const { data: astronomy, loading: astronomyLoading, error: astronomyError } =
    useAstronomySummary(forecast)
  const [selectedNightIndex, setSelectedNightIndex] = useState(0)
  const { byDate: moonByDate, status: moonEnrichmentStatus } = useMoonEnrichment(forecast)

  const handleSearch = async (address: string) => {
    const result = await search(address)
    if (result) {
      setSelectedNightIndex(0)
    }
  }

  const selectedNight = forecast?.nights[selectedNightIndex]

  return (
    <div className="app">
      <AddressSearch onSearch={handleSearch} loading={forecastLoading} />
      <ErrorBanner message={forecastError} />

      {forecast && (
        <>
          <section className="panel location-panel">
            <h2>{forecast.location.label}</h2>
            <p className="muted">
              {forecast.location.timezone} · {forecast.location.latitude.toFixed(4)},{' '}
              {forecast.location.longitude.toFixed(4)}
            </p>
          </section>

          <section className="nights-grid">
            {forecast.nights.map((night, index) => (
              <NightForecastCard
                key={night.date}
                night={night}
                selected={index === selectedNightIndex}
                onSelect={() => setSelectedNightIndex(index)}
                moonEnrichment={moonByDate[night.date] ?? null}
                moonEnrichmentLoading={
                  moonEnrichmentStatus === 'loading' ||
                  moonEnrichmentStatus === 'partial' ||
                  moonEnrichmentStatus === 'pending'
                }
              />
            ))}
          </section>

          {selectedNight && (
            <HourlyScoreChart
              hourly={selectedNight.hourly}
              date={selectedNight.date}
              stepMinutes={forecast.score_step_minutes ?? 60}
            />
          )}

          <AstronomyEventsPanel
            timezone={forecast.location.timezone}
            nights={forecast.nights}
            priorDayDarkWindow={forecast.prior_day_dark_window}
            data={astronomy}
            loading={astronomyLoading}
            error={astronomyError}
            selectedNightDate={selectedNight?.date ?? null}
          />
        </>
      )}
    </div>
  )
}

export default App
