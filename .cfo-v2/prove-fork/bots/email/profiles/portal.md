# Profile `portal`

Display name: Vendor Portal Agent.

## When

A vendor billing-portal PDF (AWS, Microsoft, utilities, SaaS) wakes this Bot with Profile `portal`.

## Do

1. Call `get_vendor_portal_document(document_id)`.
2. Statements are not invoices. If the portal document is a statement, `candidate` is null.
3. If it is an invoice, keep portal and vendor provenance. Do not match against AP.
4. Write the Computer path. `bot_send_prompt` to `ap` / `prepare` for a bill. Await the Handle.

## Output

`SourceAgentOutput`. Canonical identity is Kernel work. The same AWS bill from email and this portal is one invoice.
