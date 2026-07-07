import { useCallback, useMemo, useState } from 'react'

import { AddressSearch } from './components/AddressSearch'
import { ApodPanel } from './components/ApodPanel'
import { AstronomyEventsPanel } from './components/AstronomyEventsPanel'
import { ErrorBanner } from './components/ErrorBanner'
import { HourlyScoreChart } from './components/HourlyScoreChart'
import { NightForecastCard } from './components/NightForecastCard'
import { PanelBlurToggle } from './components/PanelBlurToggle'
import { SkyScene } from './components/SkyScene'
import { usePanelBlurPreference } from './context/PanelBlurPreferenceContext'
import { useAstronomySummary } from './hooks/useAstronomySummary'
import { useDsoVisibility } from './hooks/useDsoVisibility'
import { useForecast } from './hooks/useForecast'
import { useMoonEnrichment } from './hooks/useMoonEnrichment'

function App() {
  const { panelBlurEnabled } = usePanelBlurPreference()
  const { data: forecast, loading: forecastLoading, error: forecastError, search } = useForecast()
  const { data: astronomy, loading: astronomyLoading, error: astronomyError } =
    useAstronomySummary(forecast)
  const { data: dsoData, loading: dsoLoading, error: dsoError } = useDsoVisibility(
    forecast,
    astronomy,
    astronomyLoading,
  )
  const [selectedNightIndex, setSelectedNightIndex] = useState(0)
  const { byDate: moonByDate, pendingDates: moonPendingDates, status: moonEnrichmentStatus } =
    useMoonEnrichment(forecast)

  const handleSearch = async (address: string) => {
    const result = await search(address)
    if (result) {
      setSelectedNightIndex(0)
    }
  }

  const selectedNight = forecast?.nights[selectedNightIndex]

  const handleSelectNight = useCallback((index: number) => {
    setSelectedNightIndex(index)
  }, [])

  const handlePlanetTimelineDateChange = useCallback(
    (date: string) => {
      if (!forecast) {
        return
      }
      const index = forecast.nights.findIndex((night) => night.date === date)
      if (index >= 0) {
        setSelectedNightIndex(index)
      }
    },
    [forecast],
  )

  const moonLoadingDates = useMemo(() => {
    if (moonEnrichmentStatus === 'loading') {
      return new Set(forecast?.nights.map((night) => night.date) ?? [])
    }
    return moonPendingDates
  }, [forecast, moonEnrichmentStatus, moonPendingDates])

  return (
    <>
      <SkyScene />
      <PanelBlurToggle />
      <div className={`app${panelBlurEnabled ? '' : ' app--no-panel-blur'}`}>
      <AddressSearch onSearch={handleSearch} loading={forecastLoading} />
      <ErrorBanner message={forecastError} />

      {!forecast && <ApodPanel />}

      {forecast && (
        <>
          <section className="panel location-panel" data-testid="location-panel">
            <h2>{forecast.location.label}</h2>
            <p className="muted">
              {forecast.location.timezone} · {forecast.location.latitude.toFixed(4)},{' '}
              {forecast.location.longitude.toFixed(4)}
            </p>
          </section>

          <div className="forecast-notice-block">
            <p className="forecast-notice muted" data-testid="forecast-notice">
              Seeing and atmospheric transparency forecasts are most reliable for the first ~3 days.
              Later nights show visibility only.
            </p>
            {forecast.astro_data_unavailable && (
              <p className="forecast-notice muted" data-testid="forecast-astro-unavailable-notice">
                Seeing and atmospheric transparency data could not be retrieved for the requested
                address/location.
              </p>
            )}
            <p className="forecast-notice muted">
              Seeing values use arcseconds (″).
            </p>
          </div>

          <section className="nights-grid" data-testid="nights-grid">
            {forecast.nights.map((night, index) => (
              <NightForecastCard
                key={night.date}
                night={night}
                selected={index === selectedNightIndex}
                onSelect={handleSelectNight}
                nightIndex={index}
                moonEnrichment={moonByDate[night.date] ?? null}
                moonEnrichmentLoading={moonLoadingDates.has(night.date)}
              />
            ))}
          </section>

          {selectedNight && (
            <HourlyScoreChart
              hourly={selectedNight.hourly}
              date={selectedNight.date}
              stepMinutes={forecast.score_step_minutes ?? 60}
              cloudCover={selectedNight.cloud_cover}
              precipitation={selectedNight.precipitation}
              astroForecastLimited={selectedNight.astro_forecast_limited ?? true}
            />
          )}

          <AstronomyEventsPanel
            timezone={forecast.location.timezone}
            nights={forecast.nights}
            priorDayDarkWindow={forecast.prior_day_dark_window}
            data={astronomy}
            loading={astronomyLoading}
            error={astronomyError}
            dsoData={dsoData}
            dsoLoading={dsoLoading}
            dsoError={dsoError}
            selectedNightDate={selectedNight?.date ?? null}
            onSelectedNightDateChange={handlePlanetTimelineDateChange}
          />
        </>
      )}
      </div>
    </>
  )
}

export default App
