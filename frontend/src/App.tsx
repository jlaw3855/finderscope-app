import { useState } from 'react'

import { AddressSearch } from './components/AddressSearch'
import { ErrorBanner } from './components/ErrorBanner'
import { HourlyScoreChart } from './components/HourlyScoreChart'
import { NightForecastCard } from './components/NightForecastCard'
import { StarChartPanel } from './components/StarChartPanel'
import { useForecast } from './hooks/useForecast'
import { useMoonEnrichment } from './hooks/useMoonEnrichment'
import { useStarChart } from './hooks/useStarChart'

function App() {
  const { data: forecast, loading: forecastLoading, error: forecastError, search } = useForecast()
  const {
    data: starChart,
    loading: chartLoading,
    error: chartError,
    generate,
  } = useStarChart()
  const [selectedNightIndex, setSelectedNightIndex] = useState(0)
  const { byDate: moonByDate, status: moonEnrichmentStatus } = useMoonEnrichment(forecast)

  const handleSearch = async (address: string) => {
    const result = await search(address)
    if (result) {
      setSelectedNightIndex(0)
    }
  }

  const handleGenerateChart = (params: {
    date: string
    time: string
    viewType: 'all-sky' | 'constellation'
    constellation?: string
  }) => {
    if (!forecast) {
      return
    }

    generate({
      latitude: forecast.location.latitude,
      longitude: forecast.location.longitude,
      date: params.date,
      time: params.time,
      view_type: params.viewType,
      constellation: params.constellation ?? null,
    })
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

          <StarChartPanel
            location={forecast.location}
            nights={forecast.nights}
            imageUrl={starChart?.image_url ?? null}
            loading={chartLoading}
            error={chartError}
            onGenerate={handleGenerateChart}
          />
        </>
      )}
    </div>
  )
}

export default App
