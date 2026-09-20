# Session 04 notes — Bot `ap`

`office/constitution.md` exists and is law. Client root is `.cfo-v2/`. Computer is `.cfo-v2/office/computer`.

This slice owns Bot `ap` Profiles `prepare` and `investigate`. Slug-map already maps those Display names and does not put AP Reviewer / Approver / Audit on `ap`.

Still missing for live Handle completion:

- Session 02 sidecar RPC Grant re-check on every Kernel op
- Session 09 Bot `ctl-pay` turning `review-match` payloads into concurrence
- A live Pi bind (`HARNESS_BOT=ap`) draining the inbox

Until those exist, `run_ap_workflow` writes next-wake records and `ctl-pay` Handle payloads under `runs/ap/` and does not post to the pay pool.

Grant constructors for AP Reviewer, AP Approver, and AP Audit stay in `.cfo/agent.py` as Compiler input. Bot `ap` does not wear them.

Tests A–D: investigator is a Profile on `ap`, not a sixteenth Bot. Same open item, same Wake slug, different Grant set.

## 2026-09-20

Kernel host is `run_ap_kernel`. It writes a match packet and a Handle `ctl-pay` / `review-match` when the proposal is APPROVE. It does not call Runner as the office bus. `run_ap_workflow` remains the patched test host.

Canonical judged bill is INV-001 via simulated mailbox MSG-ACME-INV-001. INV-S12 is a marker. Operational alias memory writes without editing `prior_cases.json`. Unreceived work Handles `close`. Vendor bank-change stays Not built.

See `docs/Agentic-update/evidence/NOTES-ap.md`.
