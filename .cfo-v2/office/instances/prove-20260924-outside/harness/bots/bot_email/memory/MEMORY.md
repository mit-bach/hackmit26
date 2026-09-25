# email memory

## Acme Supplies
- September invoice ACM-2026-4410 lands as catalog MSG-E-INV-001 / ATT-E-001 (ACM-2026-4410.pdf).
- World wake ids may be msg-acme-acm-2026-4410; list_email_candidates maps to MSG-E-INV-001.
- Kernel/ERP invoice id is NS-4410 (not the vendor invoice number string). AP get_invoice(ACM-2026-4410) fails; use NS-4410 via books ERP.
- Attachment layout: labeled Invoice Number/Date/Due/PO/Currency/Amount Due; lines desks+monitors; hash cbda5aacfb5c6a9d64688cf40f74ce2996da81975779298c4b20788813552d6e.

## Northwind Labs (CUST-001)
- Subject "Payment plan — INV-AR-007" / msg-northwind-pay-intent-inv-ar-007 is customer_payment_intent, not remittance and not payment_confirmation.
- Route collect only; never apply cash from the promise note.
- Promise language: full $12,000 ACH on 2026-09-30 for INV-AR-007; other opens stay on due dates.
