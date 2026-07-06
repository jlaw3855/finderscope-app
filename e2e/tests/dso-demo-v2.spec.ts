import { expect, test } from '@playwright/test'

import {
  mockDsoDemoApis,
  submitDenverForecastOnDemo,
} from './helpers/mock-dso-demo-api'

test.describe.configure({ mode: 'serial' })

const DEMO_V2_PATH = '/demo/dso-visibility-v2/'

test.beforeEach(async ({ page }) => {
  await mockDsoDemoApis(page, { dsoDelayMs: 400 })
})

test('v2 demo banner is visible', async ({ page }) => {
  await page.goto(DEMO_V2_PATH)
  await expect(page.getByTestId('dso-demo-banner-v2')).toBeVisible()
  await expect(page.getByTestId('dso-demo-banner-v2')).toContainText('visual polish')
})

test('v2 timeline renders with semantic-only legend and merged segments', async ({ page }) => {
  await submitDenverForecastOnDemo(page, DEMO_V2_PATH)

  await expect(page.getByTestId('dso-visibility-timeline-v2')).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('dso-site-sky-v2')).toContainText('Bortle')

  const legend = page.getByTestId('dso-visibility-legend-v2')
  await expect(legend).toBeVisible()
  await expect(legend).not.toContainText('Andromeda Galaxy')
  await expect(legend).toContainText('Forecast darkness')

  const segments = page.getByTestId('dso-timeline-segment-v2')
  await expect(segments.first()).toBeVisible()
  expect(await segments.count()).toBeLessThanOrEqual(4)

  const darknessBands = page.getByTestId('dso-timeline-darkness-v2')
  await expect(darknessBands.first()).toBeVisible()
  expect(await darknessBands.count()).toBe(1)
})

test('v2 DSO API failure leaves planet timeline visible with isolated error', async ({ page }) => {
  await mockDsoDemoApis(page, { dsoError: true })
  await submitDenverForecastOnDemo(page, DEMO_V2_PATH)

  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-error')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-timeline-v2')).toHaveCount(0)
})
