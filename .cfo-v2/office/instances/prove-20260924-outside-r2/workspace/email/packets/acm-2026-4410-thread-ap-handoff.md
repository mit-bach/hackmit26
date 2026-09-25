# AP handoff — ACM-2026-4410 thread (inbox)

## Thread

- thread_id: thr-acme-acm-2026-4410
- messages:
  - msg-acme-acm-2026-4410-confirm-001 (vendor confirm)
  - msg-acme-acm-2026-4410-confirm-001-OUT (AP asked invoice_date)
  - msg-acme-acm-2026-4410-invoice-date-001 (vendor: invoice_date 2026-09-08)

## Extracted payable fields (thread-complete; no invention)

- vendor: Acme Supplies
- vendor_invoice_number: ACM-2026-4410
- invoice_date: 2026-09-08
- amount: 12450.00
- currency: USD
- po: 101
- goods_received: affirmed by vendor
- source: inbox body (no attachment)
- document_hash (confirm msg): 3f55dbd11a7578250ae9e1400be162c527995f3f5e0f0467910e702450307cec

## Email disposition

- Initial confirm lacked invoice_date → REQUEST_MISSING_INFORMATION + outbound.
- Vendor replied with invoice_date 2026-09-08.
- Auto-route of date-reply alone labeled GOODS_RECEIPT (weak); economic document is vendor invoice confirmation with complete fields.
- Dual-intake: if ACM-2026-4410 already canonical from prior seed/intake, collapse — do not mint a second Kernel id.
- Email does not match, pay, or close.

## Request to ap / prepare

Own open bill for ACM-2026-4410 if not already registered; three-way match when ready. Invoice lookup should find canonical id.
