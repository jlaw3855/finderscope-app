# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-18

### Added

- Deep sky visibility in the main Astronomy panel (top-10 DSOs per forecast night).
- Bundled World Atlas 2015 light pollution grid (0.1°) for per-site Bortle/SQM without external API calls.
- `build_light_pollution_grid.py` to regenerate the grid from the official GFZ GeoTIFF (dev-only).

### Changed

- Site sky brightness lookup replaced lightpollutionmap HTTP with local grid bilinear sampling.
- Docker image now includes `data/light_pollution/`, `data/openngc/`, and `data/iau_meteor_showers.json`.

### Removed

- `LIGHT_POLLUTION_API_KEY` and lightpollutionmap QueryRaster integration.

## [1.0.0] - 2026-06-28

### Added

- Seven-night stargazing forecast with half-hour score steps, cloud/precipitation breakdowns, and dew point chart.
- Forecast response cache (geocode, astronomy time series, Open-Meteo weather, 7timer astro).
- Meteor shower peak badges on matching forecast nights (local IAU catalog).
- Astronomy summary: 90-day events timeline and 7-night planet visibility with civil/astro twilight windows.
- Optional NoctuaSky catalog enrichment for astronomy event subjects.
- NASA Astronomy Picture of the Day on the landing page (04:00 UTC day boundary).
- Animated sky scene background (Milky Way, stars, moon, meteors).
- Imperial / Metric unit toggle for temperature, visibility, and precipitation display.
- 7timer ASTRO seeing and atmospheric transparency on night cards and hourly panel (~3-day window).
- FreeAstro moon phase SVG enrichment with server-side cache and rate-limited queue.
- Production Docker image serving API and built SPA from a single container.
- GitHub Release workflow publishing container images to GHCR on version tags.

### Changed

- Moon scoring migrated to astronomy-engine altitude-based sky glow.
- Hourly score chart refactored to a unified left-aligned grid layout.

[1.1.0]: https://github.com/jlaw3855/finderscope-app/releases/tag/v1.1.0
[1.0.0]: https://github.com/jlaw3855/finderscope-app/releases/tag/v1.0.0
