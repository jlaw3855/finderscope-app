# Performance optimizations — deferred (Phase 3)

These items were identified in the performance audit but intentionally **not implemented** without explicit product/engineering approval. They carry higher risk of changing scores, UX, or visual regressions.

## Astronomy endpoint result cache

**Risk:** Stale events/planet data at the 90-day window edges when coordinates or dates shift.

**Prerequisite before implementation:**

- Cache key: normalized lat/lon (4 dp), timezone, sorted dates hash, catalog version
- TTL design (e.g. 6–24h) with manual invalidation on catalog bumps
- Integration tests for cache hit/miss and expiry

## Hourly chart DOM reduction / virtualization

**Risk:** UX-sensitive density in 30-minute mode.

**Prerequisite:** Design review for bar/metric density at half-hour step.

---

When any of the above is approved, re-run `./scripts/check-integrity.sh` and extend `backend/tests/test_performance_benchmarks.py` to capture before/after timings.
