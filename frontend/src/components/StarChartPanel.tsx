import { useEffect, useMemo, useState } from 'react'

import { formatHour12 } from '../lib/weather-format'
import type { LocationInfo, NightForecast } from '../types/forecast'
import type { StarChartViewType } from '../types/star-chart'

const CONSTELLATIONS = [
  { id: 'ori', label: 'Orion' },
  { id: 'uma', label: 'Ursa Major' },
  { id: 'cyg', label: 'Cygnus' },
  { id: 'leo', label: 'Leo' },
  { id: 'sco', label: 'Scorpius' },
  { id: 'gem', label: 'Gemini' },
]

const CUSTOM_TIME_PRESET = ''

interface StarChartPanelProps {
  location: LocationInfo
  nights: NightForecast[]
  imageUrl: string | null
  loading: boolean
  error: string | null
  onGenerate: (params: {
    date: string
    time: string
    viewType: StarChartViewType
    constellation?: string
  }) => void
}

function defaultTime(night: NightForecast | undefined): string {
  if (night?.best_hours.length) {
    return night.best_hours[0].start
  }
  if (night?.hourly.length) {
    return night.hourly[0].time
  }
  if (night?.dark_window) {
    return night.dark_window.start
  }
  return '22:00'
}

function formatTimeOption(time: string, night: NightForecast | undefined): string {
  const label = formatHour12(time)
  const isBest = night?.best_hours.some((window) => window.start === time)
  return isBest ? `${label} (best)` : label
}

function toTimeInputValue(time: string): string {
  return time.length >= 5 ? time.slice(0, 5) : time
}

export function StarChartPanel({
  location,
  nights,
  imageUrl,
  loading,
  error,
  onGenerate,
}: StarChartPanelProps) {
  const firstNight = nights[0]
  const [selectedDate, setSelectedDate] = useState(firstNight?.date ?? '')
  const [time, setTime] = useState(defaultTime(firstNight))
  const [viewType, setViewType] = useState<StarChartViewType>('all-sky')
  const [constellation, setConstellation] = useState('ori')

  const selectedNight = useMemo(
    () => nights.find((night) => night.date === selectedDate),
    [nights, selectedDate],
  )

  const timeOptions = useMemo(
    () => selectedNight?.hourly.map((entry) => entry.time) ?? [],
    [selectedNight],
  )

  const presetValue = timeOptions.includes(time) ? time : CUSTOM_TIME_PRESET

  useEffect(() => {
    if (firstNight) {
      setSelectedDate(firstNight.date)
      setTime(defaultTime(firstNight))
    }
  }, [firstNight])

  const handleDateChange = (date: string) => {
    setSelectedDate(date)
    const night = nights.find((entry) => entry.date === date)
    setTime(defaultTime(night))
  }

  const handlePresetChange = (presetTime: string) => {
    if (presetTime) {
      setTime(presetTime)
    }
  }

  const handleGenerate = () => {
    onGenerate({
      date: selectedDate,
      time,
      viewType,
      constellation: viewType === 'constellation' ? constellation : undefined,
    })
  }

  return (
    <section className="panel star-chart-panel">
      <h2>Star Chart</h2>
      <p className="muted">
        Sky map for {location.label} ({location.latitude.toFixed(2)}, {location.longitude.toFixed(2)})
      </p>

      <div className="chart-controls">
        <label>
          Date
          <select
            value={selectedDate}
            onChange={(e) => handleDateChange(e.target.value)}
            disabled={loading}
          >
            {nights.map((night) => (
              <option key={night.date} value={night.date}>
                {night.date}
              </option>
            ))}
          </select>
        </label>

        <label className="chart-time-field">
          Time
          <div className="chart-time-controls">
            <select
              value={presetValue}
              onChange={(e) => handlePresetChange(e.target.value)}
              disabled={loading || timeOptions.length === 0}
              aria-label="Quick pick dark hour"
              data-testid="chart-time-preset"
            >
              <option value={CUSTOM_TIME_PRESET}>
                {timeOptions.length === 0 ? 'No dark hours available' : 'Quick pick…'}
              </option>
              {timeOptions.map((option) => (
                <option key={option} value={option}>
                  {formatTimeOption(option, selectedNight)}
                </option>
              ))}
            </select>
            <input
              type="time"
              value={toTimeInputValue(time)}
              onChange={(e) => setTime(e.target.value)}
              disabled={loading}
              aria-label="Custom chart time"
              data-testid="chart-time-custom"
            />
          </div>
        </label>

        <label>
          View
          <select
            value={viewType}
            onChange={(e) => setViewType(e.target.value as StarChartViewType)}
            disabled={loading}
          >
            <option value="all-sky">All Sky</option>
            <option value="constellation">Constellation</option>
          </select>
        </label>

        {viewType === 'constellation' && (
          <label>
            Constellation
            <select
              value={constellation}
              onChange={(e) => setConstellation(e.target.value)}
              disabled={loading}
            >
              {CONSTELLATIONS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
        )}

        <button
          type="button"
          data-testid="generate-chart"
          onClick={handleGenerate}
          disabled={loading || !selectedDate}
        >
          {loading ? 'Generating…' : 'Generate Chart'}
        </button>
      </div>

      {error && <p className="inline-error">{error}</p>}

      <div className="chart-image-container">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt="Generated star chart"
            className="chart-image"
            data-testid="chart-image"
          />
        ) : (
          <p className="muted chart-placeholder">
            Choose a date and time, then generate a star chart.
          </p>
        )}
      </div>
    </section>
  )
}
