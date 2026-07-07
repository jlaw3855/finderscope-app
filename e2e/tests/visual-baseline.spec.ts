import { expect, test } from '@playwright/test'

import {
  mockForecastApis,
  mockMeteorPeakForecastApis,
  submitDenverForecast,
} from './helpers/mock-api'

test.describe.configure({ mode: 'serial' })

test.describe('Visual baselines', () => {
  test('search panel', async ({ page }) => {
    await mockForecastApis(page)
    await page.goto('/')

    await expect(page.getByTestId('search-panel')).toHaveScreenshot('search-panel.png')
  })

  test('apod panel', async ({ page }) => {
    await mockForecastApis(page)
    await page.goto('/')

    await expect(page.getByTestId('apod-panel')).toHaveScreenshot('apod-panel.png')
  })

  test('forecast location and night cards', async ({ page }) => {
    await mockForecastApis(page)
    await submitDenverForecast(page)

    await expect(page.getByTestId('location-panel')).toHaveScreenshot('location-panel.png')
    await expect(page.getByTestId('nights-grid')).toHaveScreenshot('nights-grid.png')
  })

  test('first night card', async ({ page }) => {
    await mockForecastApis(page)
    await submitDenverForecast(page)

    await expect(page.getByTestId('night-card').first()).toHaveScreenshot('night-card-first.png')
  })

  test('hourly score chart — first night', async ({ page }) => {
    await mockForecastApis(page)
    await submitDenverForecast(page)

    await expect(page.getByTestId('hourly-score-panel')).toHaveScreenshot(
      'hourly-score-panel-first-night.png',
    )
  })

  test('hourly score chart — second night', async ({ page }) => {
    await mockForecastApis(page)
    await submitDenverForecast(page)

    await page.getByTestId('night-card').nth(1).click()
    await expect(page.getByTestId('hourly-score-panel')).toHaveScreenshot(
      'hourly-score-panel-second-night.png',
    )
  })

  test('astronomy panel', async ({ page }) => {
    await mockForecastApis(page)
    await submitDenverForecast(page)

    await expect(page.getByTestId('dso-visibility-timeline')).toBeVisible({ timeout: 5000 })

    const panel = page.getByTestId('astronomy-panel')
    await panel.scrollIntoViewIfNeeded()
    await expect(panel).toHaveScreenshot('astronomy-panel.png')
  })

  test('meteor shower peak night card', async ({ page }) => {
    await mockMeteorPeakForecastApis(page)
    await submitDenverForecast(page)

    const meteorCard = page
      .getByTestId('night-card')
      .filter({ has: page.getByTestId('meteor-shower-badges').getByText('Perseids') })

    await expect(meteorCard).toHaveScreenshot('night-card-meteor-peak.png')
  })
})
