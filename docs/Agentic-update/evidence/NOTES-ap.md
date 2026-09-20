# NOTES — AP money out (prompt 03)

Date: 2026-09-20. Disk wins.

Match and pay stay different objects. `ap` does not pay. `pay` does not execute ACH. `ctl-pay` looks for reasons to refuse.

## Judged bill

Canonical Maximor id is **INV-001** (vendor invoice ACM-2026-4410, PO-101, GR-101). Simulated mailbox `MSG-ACME-INV-001` lands it. `tools.get_invoice` finds INV-001. Dual intake does not mint a second Kernel id.

`MSG-S12` / `INV-S12` remains a marker. `get_invoice(INV-S12)` is not found. Refuse-on-empty-evidence stays. That fixture is not the product.

## T5 pay-run on the bus

Kernel host `scheduling/host.py` writes a Harness Handle `pay` → `ctl-pay` / `review-pay` under `harness/bots/bot_ctl_pay/handles/`. After concurrence, identified wires Handle `cash` with `executed` false. There is no send-as-bank Connector.

Live Routine `weekly-pay-run` did not fire: Floor `autoRoutines: false`. See `NOTES-floor-hole.md`. Kernel-only `apply_cash_and_policy_net` pytest is not office-live.

## T7 skills / BOT.md

Standing identity and must-not stay. Skills no longer copy `must_hold` as a checklist. `ctl-pay` does not wear Payment Scheduler ranking skills. Profile `investigate` stays on `ap`. No Bot `ap-investigator`.

## T9 denylist vs re-performance

Named, not unioned. `ctl-pay` / `review-match` keeps `get_case_evidence` and the named packet. It does not hold `RECORD_TOOLS`. Grain SoD forbids that Grant union. Live INV-S12 refuse was incompleteness. On a real packet the Verifier can re-perform Kernel facts from `get_case_evidence`. It cannot always rebuild three-way match from `get_invoice`. `review-pay` cannot see the candidate list it was denylisted from rebuilding. Refuse-for-wrong-rank without packet facts stays hard. Keep the denylist.

## T10 learning

Operational AP memory writes a vendor alias (`accounting_treatment=vendor_alias`) after Kernel names a similar-name pair. The next similar bill retrieves it. Precedent cannot override a live blocking `must_hold` (duplicate still HOLD). A human editing `prior_cases.json` is not the happy path. Kernel-live. Not office-live Pi. `ap.vendor_bank_change` stays **Not built**.

## T11 / T12

INV-S12 stub Handles are history. The judged path is INV-001.

## T13 host

`run_ap_kernel` is the office-shaped host. It does not call `Runner.run_sync`. `run_ap_workflow` remains a Kernel test host so existing patched `run_agent` tests still run. Constitution still voids Runner as the Bot bus. Do not tell a judge to run `run_ap_workflow` as the office.

## Unreceived

INV-015-class not-received work Handles `close` / `coordinate`. That Handle is not approval.

## Proof

```bash
PYTHONPATH=.cfo .cfo/.venv/bin/python -m pytest .cfo/tests/test_ap_office.py .cfo/tests/test_scheduling.py .cfo/tests/test_workflow.py .cfo/tests/test_skills.py -q
PYTHONPATH=.cfo-v2/office python3 -m compiler --phase operational
```
