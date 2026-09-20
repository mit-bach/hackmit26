# Session 02 notes

Sidecar landed as `python -m cfo_kernel` with `PYTHONPATH=.cfo`. Not a Bot.

Session 00 Computer is `.cfo-v2/office/computer`. Session 01 compiled `cfo/catalog.json` and `cfo/grants.json` onto that Computer. Session 07 already persisted cash `bind_case` as `cash_recon.case_store`. This session:

- Serves RPC and re-checks Grants against that Catalog
- Points DATA_DIR / RUNS at the Computer (see `office/computer/ENV.md`)
- Calls host-side `kernel.bind_cash_case` into the existing case store
- Persists AP overlay (`runs/ingestion/overlay.json`) and BS packets (`runs/bs_recon/packets/`)
- Symlinks `$HARNESS_COMPUTER/data` → `.cfo/data`

Isolated pytest fixtures live in `office/sessions/02-fixtures/` so sidecar tests do not depend on a later compiler rewrite.

Handle completion was not live-proven. No Pi turn. No `HARNESS_BOT` bind.
