import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { CelestialAlmanacTable } from './CelestialAlmanacTable'

describe('CelestialAlmanacTable', () => {
  it('renders rise, transit, and set columns', () => {
    const html = renderToStaticMarkup(
      <CelestialAlmanacTable
        date="2026-06-27"
        rows={[
          {
            body: 'Jupiter',
            rise_at: '20:15',
            transit_at: '01:05',
            set_at: '05:40',
            transit_altitude_deg: 48,
            always_up: false,
            always_down: false,
          },
        ]}
      />,
    )

    expect(html).toContain('Jupiter')
    expect(html).toContain('20:15')
    expect(html).toContain('01:05')
    expect(html).toContain('05:40')
    expect(html).toContain('48°')
  })

  it('shows always up label when body never sets', () => {
    const html = renderToStaticMarkup(
      <CelestialAlmanacTable
        date="2026-06-27"
        rows={[
          {
            body: 'Polaris',
            rise_at: null,
            transit_at: '02:00',
            set_at: null,
            transit_altitude_deg: 40,
            always_up: true,
            always_down: false,
          },
        ]}
      />,
    )

    expect(html).toContain('Always up')
  })
})
