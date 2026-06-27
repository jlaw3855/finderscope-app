"""NoctuaSky skysources spike notes (June 2026).

Official Swagger: https://api.noctuasky.com/api/v1/swaggerdoc/
Base URL: https://api.noctuasky.com/api/v1/

Public endpoints (no API key):
- GET /skysources/?q={str}&limit={n} — catalog search (~2–3s typical)
- GET /skysources/name/{name} — exact name lookup

JWT-only (not used by Finderscope): /locations/, /observations/

Response shape (representative):
- short_name, types[], interest (float), names[] (aliases), model (e.g. jpl_sso, dso)

Failure modes:
- Timeouts on some routes (e.g. /skysources/stats/) — enrichment is fail-open
- GET /astronomical-events returns 404 — not part of official API; do not use
- Meteor shower names (Perseids, perseid) return [] — use local IAU catalog for events

Finderscope role: metadata enrichment only via noctua.py + noctua_cache.py;
event discovery remains astronomy-engine + iau_meteor_showers.json.
"""
