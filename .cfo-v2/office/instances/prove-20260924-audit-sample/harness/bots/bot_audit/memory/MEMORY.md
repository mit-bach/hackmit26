# audit

## Standing

- Profile interpret: read getters only on this instance Catalog; no sample/control/reperf/ReportStats ops.
- Never invent finding_id; HUMAN_REVIEW stays fail-closed on object; no ask_user.
- Writes: workspace/audit/ only (runs/audit/ blocked on this desk).

## 2026-09 prove-20260924-audit-sample

- Period CLOSED CLOSE-2026-09.
- Packet: workspace/audit/packets/2026-09-interpretation.json
- Report: workspace/audit/packets/report.md
- finding_ids: [] — observations only (SOD APR-INV-SELF INV-009; PAY-AP-009/010 initiator=approver USR-PAY-01; REC-NS-1240 HUMAN_REVIEW; op HOLD dup INV-006/007).
- bot_send_prompt not registered; report written in-profile.
