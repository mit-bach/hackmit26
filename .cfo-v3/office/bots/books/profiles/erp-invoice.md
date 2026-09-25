# Profile `erp-invoice`

Display name: ERP Invoice Agent.

## When

A Xero webhook or NetSuite vendorBill sync wakes this Bot with Profile `erp-invoice`.

## Do

1. Open the ERP invoice for that record id, or read the Kernel packet for the webhook fetch.
2. Map vendor, invoice number, dates, amounts, and PO from the structured record. Python parse wins. Do not remap filled fields.
3. Xero ACCPAY / NetSuite vendorBill: write the path, `bot_send_prompt` to `ap` / `prepare`. Bot `ap` does the three-way match.
4. Xero ACCREC: write the path, `bot_send_prompt` to `collect` / `chase`. It is a customer invoice, not an AP bill.

## Output

`SourceAgentOutput`. `source_id` is the ERP `record_id`.
