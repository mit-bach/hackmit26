# Books

Standing notes for this Bot. Not shared.

## Maximor / erp-invoice (2026-09)

- Entity: CO-MAXIMOR Maximor Demo Corp USD
- Lock: 2026-08 CLOSED (CLOSE-2026-08); 2026-09 OPEN
- Vendor master: data/vendors.json (340); Customer master: data/customers.json (17)
- ERP period 2026-09: NS-4410 NetSuite vendorBill Acme / ACM-2026-4410 / 12450 → workspace/books/erp/NS-4410.source.json → ap prepare ACK (mapped INV-001)
- Open AR roster: workspace/books/ar/open_invoices.json (99 invoices, 34811818.00) → collect chase ACK intake only, no dun
- Discovery: workspace/books/masters/discovery.json
- Lock read path: workspace/books/lock/period_lock_state.json (not handed to close this wake; Operator said do not close)
