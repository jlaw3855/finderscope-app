import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import type { Page } from '@playwright/test'

const fixturesDir = join(process.cwd(), 'fixtures')

export type NightForecast = {
  date: string
  meteor_showers: Array<{ id: string; name: string; zhr_nominal: number | null }>
  hourly: Array<{ at: string }>
  [key: string]: unknown
}

export type ForecastResponse = {
  nights: NightForecast[]
  [key: string]: unknown
}

const METEOR_PEAK_DATE = '2026-08-12'
const RICH_TEMPLATE_DATE = '2026-08-09'

function readFixture(name: string): string {
  return readFileSync(join(fixturesDir, name), 'utf8')
}

export function loadForecastFixture(): ForecastResponse {
  return JSON.parse(readFixture('forecast-response.json')) as ForecastResponse
}

export function buildMeteorPeakPreviewForecast(): ForecastResponse {
  const forecast = loadForecastFixture()
  const template = forecast.nights.find((night) => night.date === RICH_TEMPLATE_DATE)
  const meteorNight = forecast.nights.find((night) => night.date === METEOR_PEAK_DATE)
  if (!template || !meteorNight) {
    throw new Error('Expected Aug 9 template and Aug 12 meteor peak in forecast fixture')
  }

  const shiftTimestamp = (value: string) =>
    value.replaceAll('2026-08-09', '2026-08-12').replaceAll('2026-08-10', '2026-08-13')

  return {
    ...forecast,
    nights: forecast.nights.map((night) => {
      if (night.date !== METEOR_PEAK_DATE) {
        return night
      }

      return {
        ...template,
        date: METEOR_PEAK_DATE,
        moon_phase: meteorNight.moon_phase,
        moon_illumination: meteorNight.moon_illumination,
        moonrise: meteorNight.moonrise,
        moonset: meteorNight.moonset,
        dark_window: meteorNight.dark_window,
        meteor_showers: meteorNight.meteor_showers,
        hourly: template.hourly.map((entry) => ({
          ...entry,
          at: shiftTimestamp(entry.at),
        })),
      }
    }),
  }
}

function buildMeteorPeakMoonEnrichment(): string {
  const moon = JSON.parse(readFixture('moon-enrichment-response.json')) as {
    entries: Array<{ date: string; [key: string]: unknown }>
    [key: string]: unknown
  }

  const peakEntry = moon.entries.find((entry) => entry.date === METEOR_PEAK_DATE)
  if (!peakEntry) {
    throw new Error('Expected Aug 12 moon enrichment entry in fixture')
  }

  return JSON.stringify({
    ...moon,
    entries: [peakEntry],
    cached_count: 1,
  })
}

type MockForecastOptions = {
  forecast?: ForecastResponse
  moonEnrichmentBody?: string
}

export async function mockForecastApis(page: Page, options: MockForecastOptions = {}): Promise<void> {
  const forecastBody = JSON.stringify(options.forecast ?? loadForecastFixture())
  const moonEnrichmentBody = options.moonEnrichmentBody ?? readFixture('moon-enrichment-response.json')
  const moonVisualFixture = readFixture('moon-visual.svg')

  await page.route('**/api/forecast', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: forecastBody,
    })
  })

  await page.route('**/api/astronomy', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: readFixture('astronomy-response.json'),
    })
  })

  await page.route('**/api/moon/enrichment**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: moonEnrichmentBody,
    })
  })

  await page.route('**/api/moon/visual/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/svg+xml',
      body: moonVisualFixture,
    })
  })
}

export async function mockMeteorPeakForecastApis(page: Page): Promise<void> {
  await mockForecastApis(page, {
    forecast: buildMeteorPeakPreviewForecast(),
    moonEnrichmentBody: buildMeteorPeakMoonEnrichment(),
  })
}

export async function submitDenverForecast(page: Page): Promise<void> {
  await page.goto('/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()
  await page.getByTestId('night-card').first().waitFor({ state: 'visible' })
  await page.getByTestId('moon-visual').first().waitFor({ state: 'visible' })
}
