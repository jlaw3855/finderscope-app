# Production deployment

Finderscope **v1.1.0** ships as a **single Docker container** that serves the built React SPA and FastAPI backend on one origin (`/` + `/api/*`). Browsers call relative `/api` paths, so no separate frontend host is required.

## What ships in the container

| Capability | Runtime dependency |
|------------|------------------|
| 7-night stargazing forecast | IPGeolocation.io + Open-Meteo (+ optional 7timer ASTRO) |
| Astronomy events + planet timeline | Local [astronomy-engine](https://pypi.org/project/astronomy-engine/) |
| **Deep sky visibility (DSO)** | Bundled OpenNGC catalog + World Atlas light pollution grid (**no external API**) |
| Meteor shower peak badges | Bundled IAU catalog JSON |
| Moon phase SVG enrichment | Optional FreeAstro API key |
| Landing-page APOD | NASA Open API key (defaults to `DEMO_KEY`) |

Site Bortle/SQM for DSO contrast uses a **local World Atlas 2015 grid** (0.1° resolution). There is **no** lightpollutionmap API key and no outbound call for site sky brightness.

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **IPGeolocation API key** | Required — geocoding and astronomy time series |
| **Persistent disk** | Mount writable cache directories under `DATA_DIR` (see [Persistent storage](#persistent-storage)) |
| **HTTPS** | Terminate TLS at your platform load balancer or reverse proxy |
| **Optional keys** | `NASA_API_KEY` (APOD), `FREEASTRO_API_KEY` (moon SVG enrichment) |

### Bundled read-only data (in image)

These files are copied into the image at build time. No API key or download step is required at deploy time.

| Path in image | Size (approx.) | Purpose | License |
|---------------|----------------|---------|---------|
| `data/light_pollution/world_atlas_grid.json` | ~32 MB | Site Bortle/SQM for DSO contrast ([World Atlas 2015](https://doi.org/10.5880/GFZ.1.4.2016.001)) | CC BY-NC 4.0 |
| `data/openngc/NGC.csv` | ~3.7 MB | Deep sky object catalog | CC-BY-SA-4.0 |
| `data/iau_meteor_showers.json` | small | Meteor shower peak badges | Project catalog |

The first `POST /api/dso-visibility` request **per uvicorn worker** parses the light pollution grid into memory (~50 MB RAM); later lookups are in-memory bilinear samples. DSO ranking itself is local CPU over OpenNGC.

**World Atlas licensing:** CC BY-NC 4.0 restricts **non-commercial** use. Review compliance before deploying a public or commercial service.

### Build context note (maintainers)

The root [`.dockerignore`](../.dockerignore) excludes only **writable cache directories** (`forecast_cache/`, `moon_cache/`, `noctua_cache/`). Do not add a blanket `backend/data/` ignore rule — that breaks the release image build (bundled artifacts must reach the Docker context).

To regenerate the light pollution grid from the official GFZ GeoTIFF (dev-only):

```bash
cd backend
pip install -r scripts/requirements-build.txt
python scripts/build_light_pollution_grid.py --input /path/to/World_Atlas_2015.tif
```

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

3. Open **http://localhost:8000** and search for a location. After the forecast loads, expand **Astronomy** to see planet visibility and **Deep sky visibility**.

4. Smoke test helper:

```bash
chmod +x scripts/smoke-prod.sh
./scripts/smoke-prod.sh
```

Forecast, moon, and Noctua caches persist in the Docker volumes declared in [`docker-compose.yml`](../docker-compose.yml).

## Persistent storage

Runtime SQLite caches live under `DATA_DIR` (default `/app/data`):

| Subdirectory | Contents |
|--------------|----------|
| `forecast_cache/` | Geocode, astronomy time series, Open-Meteo weather, 7timer ASTRO |
| `moon_cache/` | FreeAstro moon SVGs and quota state |
| `noctua_cache/` | NoctuaSky skysource responses |

**Important:** Bundled catalogs and the light pollution grid also live under `/app/data/…` in the image. Mounting a **single empty named volume** at `/app/data` hides those bundled files on first use, which breaks DSO visibility and meteor shower badges.

Mount **cache subdirectories only** (as in `docker-compose.yml`), or bind equivalent paths on your platform. Bundled read-only files then remain visible from the image layer.

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
| `HTTP_TRUST_ENV` | `true` (default); set `false` if system proxy env vars break outbound API calls |

Removed in v1.1.0: `LIGHT_POLLUTION_API_KEY` (lightpollutionmap) — no longer used.

See [`backend/.env.example`](../backend/.env.example) for the full list and defaults.

## External API usage (production)

| Endpoint | Paid / external calls on cache miss |
|----------|-------------------------------------|
| `POST /api/forecast` | IPGeolocation (geocode + astronomy) + Open-Meteo; optional 7timer |
| `POST /api/astronomy` | None (local); optional Noctua when enrichment enabled |
| `POST /api/dso-visibility` | **None** (OpenNGC + World Atlas grid are local) |
| `GET /api/apod` | NASA (once per UTC day) |
| Moon enrichment routes | FreeAstro when enabled and not cached |

## GitHub Container Registry image

Current release: **v1.1.0**

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
  -v finderscope-forecast-cache:/app/data/forecast_cache \
  -v finderscope-moon-cache:/app/data/moon_cache \
  -v finderscope-noctua-cache:/app/data/noctua_cache \
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
- Attach **persistent volumes** for `forecast_cache`, `moon_cache`, and `noctua_cache` under `/app/data/` (not the entire `/app/data` tree unless you seed bundled files).
- Set environment variables in the platform dashboard (never commit `.env`).
- Map your custom domain; the platform handles HTTPS.

### VPS (manual)

1. Install Docker.
2. Pull the release image or build from source.
3. Run with named volumes for the three cache subdirectories (see example above).
4. Optionally put **nginx** or **Caddy** in front for TLS on port 443 → proxy to `:8000`.

## Moon cache prewarm

The scheduled workflow [`.github/workflows/moon-prewarm.yml`](../.github/workflows/moon-prewarm.yml) prewarms FreeAstro moon cache in CI when `FREEASTRO_API_KEY` is configured. For self-hosted production, run `./scripts/prewarm-moon-cache.sh` daily via cron if moon SVGs should be warm on first request.

## Health check

```bash
curl -s http://localhost:8000/health
# {"status":"ok","version":"1.1.0"}
```

The Docker image includes a `HEALTHCHECK` against this endpoint. The `version` field matches the [`VERSION`](../VERSION) file baked into the image.

## Creating a release

From `main` after changes are merged:

```bash
git pull origin main
# Update VERSION and CHANGELOG.md first
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
```

The [Release workflow](../.github/workflows/release.yml) runs the full integrity harness, builds and pushes the container image to GHCR, and creates a GitHub Release with notes from [`CHANGELOG.md`](../CHANGELOG.md).

Release checklist:

1. Bump [`VERSION`](../VERSION) and add a [`CHANGELOG.md`](../CHANGELOG.md) section.
2. Ensure version tests read from `VERSION` (not hardcoded semver strings).
3. Confirm `.dockerignore` still allows bundled `backend/data/` artifacts into the build context.
4. Push the tag; verify the Release workflow completes (integrity → Docker push → GitHub Release).

## Out of scope

- Split CDN + API hosting
- Kubernetes / Terraform manifests
- API authentication and rate limiting
- Automated custom-domain provisioning
- Runtime GeoTIFF sampling (grid is prebuilt at 0.1° in the image)
