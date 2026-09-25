# Bank inbound delivered (statement notice)

- persona: First National Operating (bank)
- sender: notices@firstnational.example
- message_id: msg-fnb-stmt-2026-09-operating-001
- thread_id: thr-fnb-stmt-2026-09-operating
- subject: September 2026 statement available — Operating Account BANK-OPERATING
- recipient: ap@hackmit-cfo.example
- delivered: true

Facts:
- Not a vendor bill / not an invoice
- Operating account BANK-OPERATING, period 2026-09
- Opening basis 14,857,217.18; as_of 2026-09-30
- Sample lines include TXN-2026-09-015 Northstar credit 12,412.40
- $12.40 book difference left unexplained
- No bank lines marked matched by world

Action for email/triage: classify. World does not run bank-rec match.
