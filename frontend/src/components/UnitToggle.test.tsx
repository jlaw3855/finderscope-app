import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { UnitToggle } from './UnitToggle'
import { withUnitProvider } from '../test/with-unit-provider'

describe('UnitToggle', () => {
  it('renders imperial and metric options with imperial active by default', () => {
    const html = renderToStaticMarkup(withUnitProvider(<UnitToggle />))
    expect(html).toContain('Imperial')
    expect(html).toContain('Metric')
    expect(html).toContain('aria-pressed="true"')
    expect(html).toContain('Imperial</button>')
  })
})
