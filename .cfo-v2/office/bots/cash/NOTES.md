# Session 07 notes — Bot `cash`

Session 02 sidecar (`python -m cfo_kernel`) has not landed. This slice persists `bind_case` in Kernel (`cash_recon.case_store`) onto `runs/cash_recon/cases/<case_id>.json` so a second process can investigate without in-memory globals.

Missing from later sessions (do not invent a second bus):

- Session 02: Kernel sidecar RPC that re-checks Grants and calls host-side `bind_case` (not a Catalog op).
- Session 09: Bot `ctl-cash` Profile `review-rec`. Fail-closed packets are written under `runs/cash_recon/handles/`. They are not live-sent. They do not auto-MATCH.

Grant constructors for Cash Reconciliation Reviewer stay in `.cfo/cash_recon/agent.py` as Compiler input. Bot `cash` does not wear that Display name.

Handle completion was not live-proven (no Pi turn). Kernel / unit proofs are in `office/sessions/07-PROOF.md`.
