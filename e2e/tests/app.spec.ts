import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { expect, test } from '@playwright/test'

const fixturesDir = join(process.cwd(), 'fixtures')
const forecastFixture = readFileSync(join(fixturesDir, 'forecast-response.json'), 'utf8')
const starChartFixture = readFileSync(join(fixturesDir, 'star-chart-response.json'), 'utf8')
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

  await page.route('**/api/star-chart', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: starChartFixture,
    })
  })
})

test('search shows forecast cards for the location', async ({ page }) => {
  await page.goto('/')

  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  await expect(page.getByRole('heading', { name: forecastData.location.label })).toBeVisible()
  await expect(page.getByTestId('night-card')).toHaveCount(7)
})

test('selecting another night updates the hourly chart', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  const cards = page.getByTestId('night-card')
  await expect(cards).toHaveCount(7)

  await cards.nth(1).click()
  await expect(page.getByRole('heading', { name: /Hourly scores during darkness/ })).toBeVisible()
})

test('generates a star chart image from mocked API', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()

  await expect(page.getByTestId('night-card')).toHaveCount(7)
  await page.getByTestId('generate-chart').click()

  const chartImage = page.getByTestId('chart-image')
  await expect(chartImage).toBeVisible()
  await expect(chartImage).toHaveAttribute(
    'src',
    'https://example.com/finderscope-test-chart.png',
  )
})
