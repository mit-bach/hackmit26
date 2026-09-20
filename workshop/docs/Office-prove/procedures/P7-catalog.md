# P7 — Catalog

**Job.** Every operational Catalog op that has a Grant wearer is called once from that wearer without throw. `audit.tools.get_audit_ground_truth` is not callable on operational Bots. Empty Grants are HONEST-EMPTY or a named 05 hole. Forced Wakes are RUNS, not specialist INTENDED.

**Owns.** Catalog doors. Skills never grant tools.

**Must not.** Hand-edit grants.json. Call ops from the wrong Profile. Use eval Grants (`grants.eval.json`) on the prove desk (`client.json` evalPhase operational).

**Coverage claimed.** Table E in `../04-coverage.md` (101 live ops on the template). Tick from this Computer’s `cfo/catalog.json` if the length moved.

**Preconditions.** P0 INTENDED. G3 Grant ops ⊆ Catalog.

**Instance.** Coverage `prove-<date>-catalog-rN` and/or month traces. Prefer ticking from P1–P5 first so forced Wakes are remainder only.

---

## S01 — Build the remainder list

- Stimulus: none. Diff coverage.md against catalog.json on **this** Computer
- Include extras if catalog grew past 101. Live extras vs the old 89: inbox send/list/get thread/personas, close gates/packet, integrations payout trio, `cash_recon.tools.get_pipe_identifier`, `reporting.tools.get_trusted_cash_status`
- Exclude evalOnly from the must-call list. Put them on the forbidden list
- Empty Grant Display names: not a must-call. HONEST-EMPTY rows

---

## S02 — Wearer map

For each remainder op, pick Bot + Profile from slug-map + grants. One Profile per Wake.

If no wearer (op in catalog, no Grant): either sample-data/eval or a compile bug. HARD if an office Profile’s constructor lists it and Grant dropped it. SKIP if sample-data only.

---

## S03 — Forced Wake pattern

```text
profile: <profile>
Call <catalog.op.id> with Kernel ids that exist in the World pack.
If the id does not exist, call the matching list_* first.
Do not invent amounts. Do not CONCUR. Do not lock. Stop after the tool returns.
```

- RUNS: JSON return, no traceback
- HARD: throw, unknown tool, Client reject of a granted op, write op mutating beyond ownerPrefixes in a wild way (path lease violation)
- SOFT: model refuses to call — retry once with a shorter Wake. Still no call → SKIP this op on this instance, try a more literal Wake on rN+1. Three skips with a working Grant is SOFT prompt, still a hole in catalog ticks
- Write-local ops (`create_accrual`, etc.): only on the owning Profile. Prefer a P5 tick over a forced create. If you must force, use a vendor/period Kernel already expects, then you may have dirtied close. Prefer month instance already in P5, or wipe after

---

## S04 — Accrual remainder (12)

Wearer: `close` / `accrue`. Do not call `create_accrual` from coordinate.

---

## S05 — AR remainder (6)

Wearers: `apply` for cash facts/customer/precedents; `collect` for collection candidates/facts; close may read `get_ar_close_snapshot` if granted — **read grants**. Do not give collect apply facts if Grant omits them.

---

## S06 — Audit remainder (9 operational + 1 forbidden)

Wearer: `audit` / `interpret`.

S06b forbidden:

```text
profile: interpret
Call audit.tools.get_audit_ground_truth.
```

- INTENDED: Client/Kernel reject. FORBIDDEN-OK tick
- HARD: it returns holdout on operational phase

---

## S07 — BS, cash recon, FA, prepaid, close lock remainder

Wearers: close Profiles bs/assets/prepaid; cash match; `ctl-books` / `lock` for `get_close_gates` and `get_close_packet`. One Profile each.

---

## S08 — Inbox remainder (13)

Wearers: email inbox/invoice vs World counterparty vs collect send. Do not call World ops from collect unless Grant says so. `send_office_outbound` is finance only.

---

## S09 — Invoice ingestion remainder (18)

Wearers: email/books/bank Profiles matching the source. Empty list is RUNS.

---

## S10 — Memory, reporting, scheduling, AP tools remainder

Wearers: as Grants. `get_decision_memories` RUNS if granted. T10 INTENDED is not P7.

`get_prior_cases` on ap. Scheduling on pay. AP tools on ap/ctl-pay review-match.

---

## S11 — Stripe

Wearer: `stripe` / `payout` (Stripe Payout Agent). Call the three `integrations.tools` payout ops. `invoice_candidates` stays 0. Empty Display on this instance is HARD (clone/compile stale), not HONEST.

---

## S12 — Write vs read

Prefer list/get. For `create_accrual` / other writes: one Kernel-legal create is enough for RUNS. Do not spam creates to pad ticks.

---

## Done-when

- Bare min: every granted operational op has RUNS or a SKIP with “no object in pack, list returned empty” (list op itself must have RUNS)
- Forbidden op FORBIDDEN-OK
- Empty Grants HONEST-EMPTY or 05 hole named
- Demo-ready does not require P7 forced Wakes if P1–P5 already ticked the doors. P7 is the completeness net for “everything that exists does not throw”

## Forbidden

eval Grants on operational desk. Grant unions. Hand-edited catalog ticks without pi-rpc/kernel.log evidence.

## Restart

HARD on a throw: patch that Python function, wipe if write happened, replay that op’s Wake. Do not mark the op RUNS from a Kernel unit test.
