import { expect, test } from '@playwright/test'

import {
  mockDsoDemoApis,
  submitDenverForecastOnDemo,
} from './helpers/mock-dso-demo-api'

test.describe.configure({ mode: 'serial' })

test.beforeEach(async ({ page }) => {
  await mockDsoDemoApis(page, { dsoDelayMs: 400 })
})

test('demo banner is visible on the DSO demo page', async ({ page }) => {
  await page.goto('/demo/dso-visibility/')
  await expect(page.getByTestId('dso-demo-banner')).toBeVisible()
  await expect(page.getByTestId('dso-demo-banner')).toContainText('Deep sky visibility')
})

test('planet timeline appears before DSO timeline on progressive load', async ({ page }) => {
  await submitDenverForecastOnDemo(page)

  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-loading')).toBeVisible()

  await expect(page.getByTestId('dso-visibility-timeline')).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('dso-timeline-segment').first()).toBeVisible()
  await expect(page.getByTestId('dso-site-sky')).toContainText('Bortle')
})

test('DSO API failure leaves planet timeline visible with isolated error', async ({ page }) => {
  await mockDsoDemoApis(page, { dsoError: true })
  await submitDenverForecastOnDemo(page)

  await expect(page.getByTestId('planet-visibility-timeline')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-error')).toBeVisible()
  await expect(page.getByTestId('dso-visibility-timeline')).toHaveCount(0)
})
