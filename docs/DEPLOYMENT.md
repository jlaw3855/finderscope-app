# Production deployment

Finderscope ships as a **single Docker container** that serves the built React SPA and FastAPI backend on one origin (`/` + `/api/*`). Browsers call relative `/api` paths, so no separate frontend host is required.

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **IPGeolocation API key** | Required — geocoding and astronomy time series |
| **Persistent disk** | Mount writable storage at `DATA_DIR` (default `/app/data`) for SQLite caches |
| **HTTPS** | Terminate TLS at your platform load balancer or reverse proxy |
| **Optional keys** | `NASA_API_KEY` (APOD), `FREEASTRO_API_KEY` (moon SVG enrichment) |

Bundled read-only data is baked into the Docker image (no API key required):

| Path in image | Purpose |
|---------------|---------|
| `data/light_pollution/world_atlas_grid.json` | Site Bortle/SQM for DSO contrast ([World Atlas 2015](https://doi.org/10.5880/GFZ.1.4.2016.001), CC BY-NC 4.0) |
| `data/openngc/NGC.csv` | Deep sky object catalog |
| `data/iau_meteor_showers.json` | Meteor shower peak badges |

The first DSO request per worker loads the ~32 MB light pollution grid into memory; subsequent lookups are in-memory.

## Quick start (Docker Compose)

1. Copy and configure secrets:

```bash
cp backend/.env.example backend/.env
# Set IPGEOLOCATION_API_KEY (required)
```

2. Build and run:

```bash
docker compose up -d --build
```

3. Open **http://localhost:8000** and search for a location.

4. Smoke test helper:

```bash
chmod +x scripts/smoke-prod.sh
./scripts/smoke-prod.sh
```

Data persists in the Docker volume `finderscope-data`.

## Production environment variables

Set these in your host platform or `docker compose` `environment` block:

| Variable | Production value |
|----------|------------------|
| `IPGEOLOCATION_API_KEY` | Your IPGeolocation.io key (**required**) |
| `SERVE_STATIC` | `true` |
| `STATIC_DIR` | `static` (default in image) |
| `DATA_DIR` | `/app/data` |
| `CORS_ORIGINS` | Your public site URL, e.g. `https://finderscope.example.com` |
| `NASA_API_KEY` | Personal NASA Open API key (avoid shared `DEMO_KEY` limits) |
| `FREEASTRO_API_KEY` | Optional; enables moon phase SVG enrichment |
| `MOON_ENRICHMENT_ENABLED` | `true` when FreeAstro key is set |
| `FORECAST_CACHE_ENABLED` | `true` (recommended) |
| `SEVENTIMER_ENABLED` | `true` (seeing/transparency display) |
| `NOCTUA_ENRICHMENT_ENABLED` | `false` unless you want NoctuaSky event metadata |
| `LIGHT_POLLUTION_GRID_PATH` | `data/light_pollution/world_atlas_grid.json` (default; bundled in image) |

See [`backend/.env.example`](../backend/.env.example) for the full list and defaults.

## GitHub Container Registry image

Tagged releases publish to:

```text
ghcr.io/<owner>/finderscope-app:<version>
ghcr.io/<owner>/finderscope-app:latest
```

Pull and run:

```bash
docker pull ghcr.io/<owner>/finderscope-app:1.1.0
docker run -d \
  --name finderscope \
  -p 8000:8000 \
  -v finderscope-data:/app/data \
  -e IPGEOLOCATION_API_KEY=YOUR_KEY \
  -e SERVE_STATIC=true \
  -e DATA_DIR=/app/data \
  -e CORS_ORIGINS=https://your-domain.example \
  ghcr.io/<owner>/finderscope-app:1.1.0
```

Replace `<owner>` with your GitHub username or organization (lowercase).

## Platform notes

### Fly.io / Railway / Render

- Deploy the GHCR image or connect the repo and use the root `Dockerfile`.
- Expose **port 8000**.
- Attach a **persistent volume** mounted at `/app/data`.
- Set environment variables in the platform dashboard (never commit `.env`).
- Map your custom domain; the platform handles HTTPS.

### VPS (manual)

1. Install Docker.
2. Pull the release image or build from source.
3. Run with a named volume for `/app/data`.
4. Optionally put **nginx** or **Caddy** in front for TLS on port 443 → proxy to `:8000`.

## Moon cache prewarm

The scheduled workflow [`.github/workflows/moon-prewarm.yml`](../.github/workflows/moon-prewarm.yml) prewarms FreeAstro moon cache in CI when `FREEASTRO_API_KEY` is configured. For self-hosted production, run `./scripts/prewarm-moon-cache.sh` daily via cron if moon SVGs should be warm on first request.

## Health check

```bash
curl -s http://localhost:8000/health
# {"status":"ok","version":"1.0.0"}
```

The Docker image includes a `HEALTHCHECK` against this endpoint.

## Creating a release

From `main` after changes are merged:

```bash
git pull origin main
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
```

The [Release workflow](../.github/workflows/release.yml) runs integrity checks, pushes the container image to GHCR, and creates a GitHub Release with notes from [`CHANGELOG.md`](../CHANGELOG.md).

## Out of scope (v1.0.0)

- Split CDN + API hosting
- Kubernetes / Terraform manifests
- API authentication and rate limiting
- Automated custom-domain provisioning
