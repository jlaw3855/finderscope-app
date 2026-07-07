# Performance baseline

Timing benchmarks live in `backend/tests/test_performance_benchmarks.py`. Run them with:

```bash
cd backend && pytest tests/test_performance_benchmarks.py -s
```

The `-s` flag prints p50/p95 timings to stdout. Thresholds in the tests act as regression guards; re-tune after intentional optimizations.

## Hot paths

| Path | Fixture | Typical concern |
|------|---------|-----------------|
| `build_forecast()` | Denver `location.json`, `time_series.json`, `weather.json` | astronomy-engine moon altitude per darkness slot |
| `search_astronomy_events()` | Denver lat/lon | 90-day event scan |
| `compute_planet_visibility()` | 7 forecast nights | Sun twilight windows × 7 bodies |
| `compute_dso_visibility()` | 7 forecast nights + OpenNGC catalog | Fixed-coordinate horizon sampling; off main astronomy critical path |
| Forecast SQLite cache | Same fixtures | Cold store vs warm read |

## DSO visibility endpoint

`POST /api/dso-visibility` runs after `/api/astronomy` on the client and includes a light-pollution HTTP lookup plus OpenNGC horizon scoring. Benchmark guard: `compute_dso_visibility` p50 < 3s (7 Denver nights).

## Forecast cache latency

The benchmark `test_benchmark_forecast_cache_cold_vs_warm` stores then reads three cache layers (geocode, astronomy time series, weather). Warm reads should be sub-50ms on local SQLite.

Production `/api/forecast` cache behavior:

- **Miss:** geocode (if needed) → parallel time series + Open-Meteo → `build_forecast` in a worker thread.
- **Hit:** skip upstream fetches; scoring still runs on each request.

## Integrity gate

After performance changes, run the full harness from the repo root:

```bash
./scripts/check-integrity.sh
```
