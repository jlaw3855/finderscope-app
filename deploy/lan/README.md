# LAN private deployment

Run Finderscope on your home network from the prebuilt GHCR image.

**Full guide:** [docs/DEPLOYMENT-LAN.md](../../docs/DEPLOYMENT-LAN.md)

## Quick start

```bash
# From repository root:
./scripts/deploy-lan.sh
```

Or manually:

```bash
cd deploy/lan
cp .env.example .env   # set IPGEOLOCATION_API_KEY and CORS_ORIGINS
docker compose pull
docker compose up -d
```

Open **http://localhost:8000** (or `http://<host-lan-ip>:8000` from other devices on Wi‑Fi).

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | GHCR image + cache-only volumes |
| `.env.example` | Template (copy to `.env`; gitignored) |

Do not mount a volume at `/app/data` — only the cache subdirectories in the compose file.
