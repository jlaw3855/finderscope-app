import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import type { Page } from '@playwright/test'

import { loadForecastFixture, mockForecastApis, submitDenverForecast } from './mock-api'

const fixturesDir = join(process.cwd(), 'fixtures')

function readFixture(name: string): string {
  return readFileSync(join(fixturesDir, name), 'utf8')
}

type MockDsoDemoOptions = {
  dsoDelayMs?: number
  dsoError?: boolean
}

export async function mockDsoDemoApis(
  page: Page,
  options: MockDsoDemoOptions = {},
): Promise<void> {
  await mockForecastApis(page)

  await page.route('**/api/dso-visibility', async (route) => {
    if (options.dsoError) {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'DSO service unavailable' }),
      })
      return
    }

    if (options.dsoDelayMs && options.dsoDelayMs > 0) {
      await new Promise((resolve) => {
        setTimeout(resolve, options.dsoDelayMs)
      })
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: readFixture('dso-visibility-response.json'),
    })
  })
}

export async function submitDenverForecastOnDemo(page: Page): Promise<void> {
  await page.goto('/demo/dso-visibility/')
  await page.getByLabel('Address').fill('Denver, CO')
  await page.getByRole('button', { name: 'Get Forecast' }).click()
  await page.getByTestId('night-card').first().waitFor({ state: 'visible' })
  await page.getByTestId('moon-visual').first().waitFor({ state: 'visible' })
}

export { loadForecastFixture, submitDenverForecast }
