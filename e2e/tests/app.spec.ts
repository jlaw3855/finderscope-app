import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { expect, test } from '@playwright/test'

import { loadForecastFixture, mockForecastApis, submitDenverForecast } from './helpers/mock-api'

const forecastData = loadForecastFixture()

test.describe.configure({ mode: 'serial' })

test.beforeEach(async ({ page }) => {
  await mockForecastApis(page)
})

test('search shows forecast cards for the location', async ({ page }) => {
  await submitDenverForecast(page)

  await expect(page.getByRole('heading', { name: forecastData.location.label })).toBeVisible()
  await expect(page.getByTestId('night-card')).toHaveCount(7)
  await expect(page.getByTestId('moon-visual').first()).toBeVisible()
})

test('landing page shows APOD and hides it after forecast search', async ({ page }) => {
  await page.goto('/')

  const apodPanel = page.getByTestId('apod-panel')
  await expect(apodPanel).toBeVisible()
  await expect(apodPanel.getByText('Starlink over Orion')).toBeVisible()
  await expect(apodPanel.getByText(/Credit & copyright:/)).toBeVisible()

  await submitDenverForecast(page)

  await expect(page.getByTestId('apod-panel')).toHaveCount(0)
})

test('selecting another night updates the hourly chart', async ({ page }) => {
  await submitDenverForecast(page)

  const cards = page.getByTestId('night-card')
  await expect(cards).toHaveCount(7)

  await expect(page.locator('.hourly-score-value').first()).toBeVisible()

  await cards.nth(1).click()
  await expect(page.getByRole('heading', { name: /scores during darkness/ })).toBeVisible()
})

test('shows astronomy events and planet timeline after forecast', async ({ page }) => {
  await submitDenverForecast(page)

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

test('shows deep sky visibility after astronomy loads', async ({ page }) => {
  await mockForecastApis(page, { dsoDelayMs: 400 })
  await submitDenverForecast(page)

  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-loading')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-timeline')).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('dso-site-sky')).toContainText('Bortle')
  await expect(page.getByTestId('dso-timeline-segment').first()).toBeVisible()
})

test('DSO API failure leaves planet timeline visible with isolated error', async ({ page }) => {
  await mockForecastApis(page, { dsoError: true })
  await submitDenverForecast(page)

  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-error')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-timeline')).toHaveCount(0)
})
