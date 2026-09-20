"""Internal schema map discovered from existing workflow contracts.

Do not invent a parallel schema. Generated artifacts use these fields,
keys, and amount/date representations exactly.

domain | existing file/model | required fields | PK | FKs | amount | date | output
-------|---------------------|-----------------|----|-----|--------|------|-------
AP invoice | data/invoices.json Invoice | invoice_id, vendor, amount, invoice_date, due_date, vendor_invoice_number | invoice_id | po_id | float USD | YYYY-MM-DD | invoices.json
Purchase order | data/purchase_orders.json PurchaseOrder | po_id, vendor, authorized_amount, status | po_id | vendor | float USD | YYYY-MM-DD | purchase_orders.json
Goods receipt | data/goods_receipts.json GoodsReceipt | receipt_id, po_id, received, amount_received, quantity_* | receipt_id | po_id | float + int qty | YYYY-MM-DD | goods_receipts.json
AR customer | data/ar_customers.json Customer | customer_id, customer_name | customer_id | | | | ar_customers.json
AR invoice | data/ar_invoices.json CustomerInvoice | invoice_id, customer_id, original_amount, outstanding_amount, dates | invoice_id | customer_id | float USD | YYYY-MM-DD | ar_invoices.json
AR payment | data/ar_payments.json CustomerPayment | payment_id, amount, payment_date, payer_name | payment_id | customer_id | float USD | YYYY-MM-DD | ar_payments.json
Cash bank | data/cash_recon/bank_statement.json BankTransaction | transaction_id, date, amount | transaction_id | | float + amount_minor cents | YYYY-MM-DD | cash_recon/bank_statement.json
Cash ledger | data/cash_recon/ledger.json LedgerEntry | entry_id, date, amount, account | entry_id | | float + amount_minor cents | YYYY-MM-DD | cash_recon/ledger.json
Stripe payout | integrations.models.ProviderPayout | payout_id, amount (cents), lines | payout_id | | int cents | unix/ISO | integrations/stripe/
Close prepaid | data/close/prepaids.json PrepaidItem | prepaid_id, total_amount, start/end | prepaid_id | source_document_id | float USD | YYYY-MM-DD | close/prepaids.json
Close asset | data/close/fixed_assets.json FixedAsset | asset_id, cost, useful_life_months | asset_id | source_document_id | float USD | YYYY-MM-DD | close/fixed_assets.json
Audit invoice | data/audit/invoices.json AuditInvoice | invoice_id, vendor, vendor_invoice_number, amount | invoice_id | vendor_id | float USD | YYYY-MM-DD | audit/invoices.json
Audit payment | data/audit/payments.json AuditPayment | payment_id, amount, vendor_id | payment_id | invoice_ids, approval_ids | float USD | YYYY-MM-DD | audit/payments.json
Reporting line | reporting.models.ReportingLine | line_id, entry_id, transaction_id, account, amount | line_id | source_document_id | float USD | YYYY-MM-DD | reporting/ledger_seed.json
Forecast line | reporting.models.ForecastLine | line_id, source_id, expected_date, amount | line_id | source_id | float USD signed | YYYY-MM-DD | reporting/forecast_lines.json
Payroll | data/reporting/payroll.json PayrollSchedule | schedule_id, pay_date, expected_amount | schedule_id | | float USD | YYYY-MM-DD | reporting/payroll.json
Accrual history | data/historical_invoices.json AccrualInvoice | invoice_id, vendor, amount, service_period | invoice_id | vendor | float USD | YYYY-MM | historical_invoices.json

Adapters (never silent copies):
- AP Invoice → AuditInvoice (same invoice_id, amount, vendor_invoice_number)
- Vendor → AuditVendor (vendor_id + normalize_vendor name)
- VendorPayment → BankTransaction + LedgerEntry (same amount_minor)
- CustomerPayment → BankTransaction + LedgerEntry
- ProviderPayout → bank deposit + cash ledger (payout.amount cents)
- JournalEntry → ReportingLine pair + AuditJournalEntry
- PrepaidItem / FixedAsset → close seed files + reporting opex lines
"""

SCHEMA_VERSION = "2026.09-cfo-sample-2"
