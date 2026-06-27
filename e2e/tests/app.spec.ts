import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { expect, test } from '@playwright/test'

const fixturesDir = join(process.cwd(), 'fixtures')
const forecastFixture = readFileSync(join(fixturesDir, 'forecast-response.json'), 'utf8')
const astronomyFixture = readFileSync(join(fixturesDir, 'astronomy-response.json'), 'utf8')
const moonEnrichmentFixture = readFileSync(
  join(fixturesDir, 'moon-enrichment-response.json'),
  'utf8',
)
const moonVisualFixture = readFileSync(join(fixturesDir, 'moon-visual.svg'), 'utf8')
const forecastData = JSON.parse(forecastFixture) as {
  location: { label: string }
}

test.describe.configure({ mode: 'serial' })

test.beforeEach(async ({ page }) => {
  await page.route('**/api/forecast', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: forecastFixture,
    })
  })

  await page.route('**/api/astronomy', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: astronomyFixture,
    })
  })

  await page.route('**/api/moon/enrichment**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: moonEnrichmentFixture,
    })
  })

  await page.route('**/api/moon/visual/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/svg+xml',
      body: moonVisualFixture,
    })
  })
})

test('search shows forecast cards for the location', async ({ page }) => {
  await page.goto('/')

  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  await expect(page.getByRole('heading', { name: forecastData.location.label })).toBeVisible()
  await expect(page.getByTestId('night-card')).toHaveCount(7)
  await expect(page.getByTestId('moon-visual').first()).toBeVisible()
})

test('selecting another night updates the hourly chart', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  const cards = page.getByTestId('night-card')
  await expect(cards).toHaveCount(7)

  await expect(page.locator('.hourly-score-value').first()).toBeVisible()

  await cards.nth(1).click()
  await expect(page.getByRole('heading', { name: /scores during darkness/ })).toBeVisible()
})

test('shows astronomy events and planet timeline after forecast', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  await expect(page.getByTestId('night-card')).toHaveCount(7)
  await expect(page.getByTestId('meteor-shower-badges')).toBeVisible()
  await expect(page.getByTestId('meteor-shower-badges').getByText('Perseids')).toBeVisible()
  await expect(page.getByTestId('astronomy-panel')).toBeVisible()
  await expect(page.getByTestId('astronomy-events-list')).toBeVisible()
  await expect(page.getByTestId('planet-timeline-date-select')).toBeVisible()
  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('planet-timeline-darkness').first()).toBeVisible()
  await expect(page.getByTestId('planet-timeline-segment').first()).toBeVisible()
  await expect(page.getByTestId('planet-visibility-details')).toBeVisible()

  await page.getByTestId('planet-timeline-date-select').selectOption({ index: 1 })
  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('planet-timeline-darkness')).toHaveCount(2)
})
