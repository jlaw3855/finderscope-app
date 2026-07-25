import type { CelestialAlmanacRow } from '../types/astronomy'
import {
  formatAlmanacTime,
  formatPeakAltitude,
} from '../lib/astronomy-format'

interface CelestialAlmanacTableProps {
  date: string
  rows: CelestialAlmanacRow[]
}

export function CelestialAlmanacTable({ date, rows }: CelestialAlmanacTableProps) {
  return (
    <div className="celestial-almanac-wrap">
      <table
        className="celestial-almanac-table"
        data-testid="celestial-almanac-table"
        aria-label={`Rise, transit, and set times for ${date}`}
      >
        <thead>
          <tr>
            <th scope="col">Body</th>
            <th scope="col">Rise</th>
            <th scope="col">Transit</th>
            <th scope="col">Set</th>
            <th scope="col">Transit alt</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.body} data-testid="celestial-almanac-row">
              <th scope="row">{row.body}</th>
              <td>{formatAlmanacTime(row.rise_at, row.always_up, row.always_down, 'rise')}</td>
              <td>{formatAlmanacTime(row.transit_at, row.always_up, row.always_down)}</td>
              <td>{formatAlmanacTime(row.set_at, row.always_up, row.always_down, 'set')}</td>
              <td>{formatPeakAltitude(row.transit_altitude_deg)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
