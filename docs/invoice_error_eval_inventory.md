# Invoice error evaluation inventory

Recovered from generators, answer keys, inbox fixtures, holdout contracts, and handwritten AP fixtures.
PASS/FAIL in the table is **after** justified kernel repairs. Baseline (pre-fix) metrics and the 17 incorrect IDs are in `runs/evals/invoice_error_detection_baseline.json` and `docs/invoice_error_detection_report.md`.

Current results are from the 15-agent kernel path: `decide_ap(live=False)`, `classify_text`, `inbox.handoff`, `policy_eligible_for_pool`.
The old 43-agent `run_ap_workflow` was not used.

Total cases in this pack: **91**.

| CASE ID | SOURCE FILE | DOCUMENT TYPE | PLANTED ERROR | EXPECTED AGENT BEHAVIOR | EXPECTED FINANCE OUTCOME | CURRENT RESULT | PASS/FAIL | NOTES |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEMO-INV-001 | `sample_data/agents/ap_ar.py:_ap_cases / data/demo/invoices.json` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Clean three-way match SCN-AP-001. Must not flag. Already paid via PAY-AP-001 so must not be scheduled again. |
| DEMO-INV-002 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Clean AWS invoice due this week SCN-AP-009. |
| DEMO-INV-003 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | partial_receipt | HOLD | HOLD | HOLD / partial_receipt | PASS | SCN-AP-002 quantity mismatch: 50 billed/ordered, 40 received. Repo exception type is partial_receipt. |
| DEMO-INV-004 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | material_amount_mismatch | HOLD | HOLD | HOLD / material_amount_mismatch | PASS | SCN-AP-003 Slack billed $5000 vs PO $4375. |
| DEMO-INV-005 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | SCN-AP-004 missing goods receipt. |
| DEMO-INV-006 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | SCN-AP-005 original of SV-999001. |
| DEMO-INV-007 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | SCN-AP-005 peer duplicate submission. |
| DEMO-INV-008 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | po_not_approved | HOLD | HOLD | HOLD / po_not_approved,goods_not_received | PASS | SCN-AP-006 PO pending approval. |
| DEMO-INV-009 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | approval_limit_exceeded | HOLD | HOLD | HOLD / approval_limit_exceeded | PASS | SCN-AP-007 $50k PO vs $10k approver limit. Also round-number / self-approval audit traps. |
| DEMO-INV-010 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | SCN-AP-008 on hold; PAY-AP-010 is the paid-while-held audit trap. |
| DEMO-INV-012 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | SCN-AP-010 clean three-way match. PAY-AP-012 already paid it early, so matching APPROVE must not reschedule. |
| DEMO-INV-013 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | SCN-AP-011 clean with open 2/10 discount. |
| DEMO-INV-014 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Clean Northline invoice; grouped ACH already paid. Must not reschedule. |
| DEMO-INV-015 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Clean Northline invoice; already paid in grouped ACH. |
| DEMO-INV-016 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Clean Northline invoice; already paid in grouped ACH. |
| DEMO-INV-017 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Helios invoice itself is a clean three-way match. Fee-netted wire is a cash-recon fact, not an AP hold. Already paid. |
| DEMO-INV-018 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Dell capital invoice. Clean match. Distinct from handwritten fixture INV-018 (duplicate). |
| DEMO-INV-019 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Hartford prepaid source invoice with full receipt. |
| DEMO-INV-020 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | missing_po | HOLD | HOLD | HOLD / missing_po | PASS | Orbit Analytics prepaid from 2025 with no PO. Must not enter the payment pool. |
| DEMO-INV-021 | `sample_data/agents/ap_ar.py:_ap_cases` | invoice | vendor_mismatch | APPROVE | APPROVE | APPROVE / vendor_mismatch | PASS | SCN-AP-013 Acme Supply Co. alias supported by August CASE-001. Exception present; payment allowed. |
| DEMO-MSG-E-INV-001 | `sample_data/agents/ap_ar.py:_ingestion / data/demo/ingestion/emails.json` | invoice | none | CLASSIFY_INVOICE | CLASSIFY_INVOICE | invoice / invoice | PASS | SCN-ING-001 true payable invoice. reason=Document contains vendor, invoice number, invoice date, and amount due |
| DEMO-MSG-E-MESSY | `sample_data/agents/ap_ar.py:_ingestion` | invoice | none | CLASSIFY_INVOICE | CLASSIFY_INVOICE | invoice / invoice | PASS | SCN-ING-002 OCR-messy but still a true invoice (1NVOICE header). reason=Document contains vendor, invoice number, invoice date, and amount due |
| DEMO-MSG-E-PO | `sample_data/agents/ap_ar.py:_ingestion` | purchase_order | purchase_order_as_invoice | NO_AP | NO_AP | purchase_order / purchase_order | PASS | SCN-ING-003 / SCN-AP-012. Must not enter AP. Official evaluate-cfo currently accepts not_invoice. reason=Purchase order/requisition, not a vendor invoice |
| DEMO-MSG-E-QUOTE | `sample_data/agents/ap_ar.py:_ingestion` | quote | quote_as_invoice | NO_AP | NO_AP | quote / quote | PASS | SCN-ING-004. reason=Document is a quote/estimate, not an invoice |
| DEMO-MSG-E-RCPT | `sample_data/agents/ap_ar.py:_ingestion` | receipt | receipt_as_invoice | NO_AP | NO_AP | receipt / receipt | PASS | SCN-ING-005 Uber receipt. Official evaluate-cfo currently accepts not_invoice. reason=Employee/paid receipt, not a vendor invoice |
| DEMO-MSG-E-STMT | `sample_data/agents/ap_ar.py:_ingestion` | statement | statement_as_invoice | NO_AP | NO_AP | statement / statement | PASS | SCN-ING-006. reason=Account statement rather than an invoice |
| DEMO-MSG-E-MKT | `sample_data/agents/ap_ar.py:_ingestion` | marketing | none | NO_AP | NO_AP | marketing / marketing | PASS | SCN-ING-007. reason=Looks like a marketing email, not a vendor invoice |
| DEMO-MSG-E-INFER | `sample_data/agents/ap_ar.py:_ingestion` | invoice | none | CLASSIFY_INVOICE | CLASSIFY_INVOICE | invoice / invoice | PASS | SCN-ING-008 vendor inferable. reason=Document contains vendor, invoice number, invoice date, and amount due |
| DEMO-MSG-E-MISSING | `sample_data/agents/ap_ar.py:_ingestion` | not_invoice | missing_required_field | NO_AP | NO_AP | not_invoice / not_invoice | PASS | SCN-ING-009 unsafe missing amount/vendor/number. reason=Mentions invoice language but is missing required invoice fields |
| DEMO-MSG-E-DUP-001 | `sample_data/agents/ap_ar.py:_ingestion` | invoice | duplicate_copy | CLASSIFY_INVOICE | CLASSIFY_INVOICE | invoice / invoice | PASS | SCN-ING-010 same invoice, different filename. Classification is invoice; registration must not create a second payable. reason=Document contains vendor, invoice number, invoice dat |
| XWF-DUP-NO-PAY | `scheduling/cash.py + decide_ap` | invoice | duplicate | HOLD | HOLD | None / duplicate | PASS | Duplicate INV-006 must not be payment-eligible. |
| XWF-PAID-NO-RESCHEDULE | `data/demo/canonical/vendor_payments.json PAY-AP-001` | invoice | already_paid | NO_PAY | NO_PAY | NO_PAY / already_paid | PASS | INV-001 matching APPROVE is correct; scheduler must not pay it again. |
| XWF-HOLDS-NOT-ELIGIBLE | `scheduling/cash.py:BLOCKING_EXCEPTIONS` | invoice | hold | NO_PAY | NO_PAY | NO_PAY / 9 | PASS | Every AP HOLD in the demo pack must be payment-ineligible. |
| MEM-ALIAS-HELP | `data/prior_cases.json CASE-001` | invoice | vendor_mismatch | APPROVE | APPROVE | APPROVE / vendor_mismatch | PASS | August CASE-001 makes September Acme alias payable. Memory helps. |
| MEM-ALIAS-CONFLICT | `tests/test_deterministic.py:test_unknown_vendor_without_prior_case_is_blocked` | invoice | vendor_mismatch | HOLD | HOLD | HOLD / vendor_mismatch | PASS | September evidence without August precedent must not copy CASE-001. Memory must not hurt. |
| FIX-INV-001 | `data/invoices.json` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | Handwritten clean three-way match. IDs collide with demo pack but facts differ. |
| FIX-INV-011 | `data/invoices.json` | invoice | small_amount_discrepancy | APPROVE | APPROVE | APPROVE / small_amount_discrepancy | PASS | Within P-009 tolerance. Must not HOLD. |
| FIX-INV-013 | `data/invoices.json` | invoice | material_amount_mismatch | HOLD | HOLD | HOLD / material_amount_mismatch | PASS | Tax above pretax PO. |
| FIX-INV-014 | `data/invoices.json` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | PO-114 has no GR. |
| FIX-INV-015 | `data/invoices.json` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | GR not received. |
| FIX-INV-016 | `data/invoices.json` | invoice | missing_po | HOLD | HOLD | HOLD / missing_po | PASS | No PO. |
| FIX-INV-017 | `data/invoices.json` | invoice | vendor_mismatch | APPROVE | APPROVE | APPROVE / vendor_mismatch | PASS | Acme Supply Co. alias with CASE-001. |
| FIX-INV-018 | `data/invoices.json` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | Duplicate of INV-010 Notion NL-INV-088421. Not the demo Dell invoice. |
| FIX-INV-019 | `data/invoices.json` | invoice | partial_receipt | HOLD | HOLD | HOLD / partial_receipt | PASS | 4 of 10 received. |
| FIX-INV-020 | `data/invoices.json` | invoice | po_not_approved | HOLD | HOLD | HOLD / po_not_approved,unusual_timing,approval_limit_exceeded | PASS | PO-120 pending. |
| ID-NORM-PUNCT | `invoice_ingestion/identity.py` | invoice | formatted_duplicate | COLLAPSE | COLLAPSE | COLLAPSE / {'slash': 'holdoutvendor:ABC23781', 'dash': 'holdoutvendor:ABC23781'} | PASS | ABC/23781 and ABC-23781 must share a canonical key. |
| ID-EXISTING-AP | `invoice_ingestion/validate.py:existing_ap_match` | invoice | duplicate | LINK | LINK | INV-010 / INV-010 | PASS | existing_ap_match must use the same invoice-number normalization as AP matching. |
| ID-EXISTING-PUNCT | `invoice_ingestion/validate.py:existing_ap_match` | invoice | formatted_duplicate | LINK | LINK | INV-010 / INV-010 | PASS | NL/INV/088421 must match stored NL-INV-088421. |
| ID-ALNUM | `tools.py:normalize_invoice_number` | invoice | none | NORMALIZE | NORMALIZE | ABC23781 / ABC23781 | PASS | Alphanumeric fold. |
| INBOX-CLEAN | `inbox/fixtures.py:spec_clean_attachment` | invoice | none | CREATE_AP | CREATE_AP | VENDOR_INVOICE / MATCHED | PASS | Clean attachment creates one canonical invoice and matches. |
| INBOX-PRICE | `inbox/fixtures.py:spec_price_mismatch` | invoice | material_amount_mismatch | HOLD | HOLD | BLOCKED / material_amount_mismatch | PASS | Office Depot $5000 vs PO-104. |
| INBOX-NO-PO | `inbox/fixtures.py:spec_no_po` | invoice | missing_po | HOLD | HOLD | NON_PO / missing_po | PASS | Datadog body invoice with no PO. |
| INBOX-QUOTE | `inbox/fixtures.py:spec_quote` | quote | quote_as_invoice | NO_AP | NO_AP | IGNORE / CONTRACT_OR_QUOTE | PASS | Quote with invoice-ready catalog language. |
| INBOX-PO | `inbox/fixtures.py:spec_purchase_order` | purchase_order | purchase_order_as_invoice | NO_AP | NO_AP | ROUTE_TO_EXISTING_WORKFLOW / PURCHASE_ORDER | PASS | Purchase order must not create AP. |
| INBOX-GR | `inbox/fixtures.py:spec_goods_receipt` | goods_receipt | receipt_as_invoice | NO_AP | NO_AP | RECORD_GOODS_RECEIPT / GOODS_RECEIPT | PASS | Goods receipt routes without creating invoice. |
| INBOX-STMT | `inbox/fixtures.py:spec_statement` | statement | statement_as_invoice | NO_AP | NO_AP | IGNORE / VENDOR_STATEMENT | PASS | Vendor statement. |
| INBOX-PAY-CONF | `inbox/fixtures.py:spec_payment` | payment_confirmation | payment_confirmation_as_invoice | NO_AP | NO_AP | RECORD_PAYMENT_NOTICE / PAYMENT_CONFIRMATION | PASS | Payment confirmation is not an unpaid invoice. |
| INBOX-CREDIT | `inbox/fixtures.py:spec_credit_memo` | credit_memo | credit_memo_as_invoice | NO_AP | NO_AP | ROUTE_TO_EXISTING_WORKFLOW / CREDIT_MEMO | PASS | Credit memo is not a payable invoice. |
| INBOX-DUP-BUSINESS | `inbox/fixtures.py:spec_business_duplicate` | invoice | duplicate | HOLD | HOLD | BUSINESS_DUPLICATE / BUSINESS_DUPLICATE | PASS | Same invoice number + vendor, different filename. Must not create second payable. |
| RESTART-DUP | `tests/test_inbox_persistence.py` | invoice | duplicate | HOLD | HOLD | BUSINESS_DUPLICATE / BUSINESS_DUPLICATE | PASS | Overlay reload after in-memory clear still recognizes the invoice; a fresh handoff is BUSINESS_DUPLICATE or DUPLICATE_DELIVERY. |
| MATH-TOTALS-OK | `invoice_ingestion/validate.py` | invoice | none | ACCEPT | ACCEPT | PASS / True | PASS | Clean subtotal+tax=total. |
| MATH-TOTALS-BAD | `invoice_ingestion/validate.py` | invoice | inconsistent_totals | REJECT | REJECT | PASS / True | PASS | Subtotal+tax != total must reject. |
| MATH-LINE-SUM | `invoice_ingestion/validate.py` | invoice | line_item_sum_mismatch | REJECT | REJECT | PASS / True | PASS | Line items 80+50 != subtotal 100. |
| MATH-CENTS | `invoice_ingestion/validate.py` | invoice | none | ACCEPT | ACCEPT | PASS / True | PASS | Cents vs dollars: $12,450 is 1,245,000 cents. |
| MATH-CENTS-CAND | `invoice_ingestion/validate.py` | invoice | none | ACCEPT | ACCEPT | PASS / True | PASS | Invoice amount stays in dollars. |
| HO-AP-001 | `discrepancy/holdout_catalog.py` | invoice | partial_receipt | HOLD | HOLD | HOLD / partial_receipt | PASS | PO 240 / GR 217 / invoice 240. |
| HO-AP-002 | `discrepancy/holdout_catalog.py` | invoice | material_amount_mismatch | HOLD | HOLD | HOLD / material_amount_mismatch | PASS | Invoice $15,478 vs PO $14,200. |
| HO-AP-003 | `discrepancy/holdout_catalog.py` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | Missing GR. |
| HO-AP-004A | `discrepancy/holdout_catalog.py` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | HX-55190 twice. |
| HO-AP-005A | `discrepancy/holdout_catalog.py` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | ABC/23781 vs ABC-23781 after alphanumeric normalization. |
| HO-AP-006 | `discrepancy/holdout_catalog.py` | invoice | approval_limit_exceeded | HOLD | HOLD | HOLD / approval_limit_exceeded | PASS | PO $72k exceeds $20k limit. |
| HO-AP-008 | `discrepancy/holdout_catalog.py` | invoice | goods_not_received | HOLD | HOLD | HOLD / goods_not_received | PASS | Held invoice must not enter payment pool. |
| ADV-QUOTE-LAYOUT | `evals/invoice_error_detection.py` | quote | quote_as_invoice | NO_AP | NO_AP | quote / quote | PASS | Quote with vendor, lines, total, valid-through. Must not become an invoice. reason=Document is a quote/estimate, not an invoice |
| ADV-ESTIMATE | `evals/invoice_error_detection.py` | quote | estimate_as_invoice | NO_AP | NO_AP | quote / quote | PASS | Estimate document. reason=Document is a quote/estimate, not an invoice |
| ADV-PO-LAYOUT | `evals/invoice_error_detection.py` | purchase_order | purchase_order_as_invoice | NO_AP | NO_AP | purchase_order / purchase_order | PASS | PO with supplier, quantities, prices, PO number, total. reason=Purchase order/requisition, not a vendor invoice |
| ADV-RECEIPT-PAID | `evals/invoice_error_detection.py` | receipt | receipt_as_invoice | NO_AP | NO_AP | receipt / receipt | PASS | Paid receipt with vendor/amount/date. reason=Employee/paid receipt, not a vendor invoice |
| ADV-BANK-CHARGE | `evals/invoice_error_detection.py` | bank_charge | bank_charge_as_invoice | NO_AP | NO_AP | not_invoice / not_invoice | PASS | Bank/card charge must not create AP. reason=Bank/card charge, not a vendor invoice |
| ADV-SHIPPING-NOTICE | `evals/invoice_error_detection.py` | shipping_notice | shipping_notice_as_invoice | NO_AP | NO_AP | not_invoice / not_invoice | PASS | Shipping notice / packing list. reason=Shipping notice/packing list, not a vendor invoice |
| ADV-CREDIT-MEMO | `evals/invoice_error_detection.py` | credit_memo | credit_memo_as_invoice | NO_AP | NO_AP | not_invoice / not_invoice | PASS | Credit memo must not become a payable invoice. reason=Credit memo/credit note, not a payable vendor invoice |
| ADV-CLEAN-INVOICE | `evals/invoice_error_detection.py` | invoice | none | CLASSIFY_INVOICE | CLASSIFY_INVOICE | invoice / invoice | PASS | Clean control invoice for classification. reason=Document contains vendor, invoice number, invoice date, and amount due |
| RT-QUOTE-PROPOSAL | `evals/invoice_error_detection.py` | quote | quote_as_invoice | NO_AP | NO_AP | quote / quote | PASS | Independent quote family: proposal + valid through. Must not become AP. reason=Document is a quote/estimate, not an invoice |
| RT-PO-ISSUED | `evals/invoice_error_detection.py` | purchase_order | purchase_order_as_invoice | NO_AP | NO_AP | purchase_order / purchase_order | PASS | Independent PO family. reason=Purchase order/requisition, not a vendor invoice |
| RT-RECEIPT-STAMP | `evals/invoice_error_detection.py` | receipt | receipt_as_invoice | NO_AP | NO_AP | receipt / receipt | PASS | Independent paid-receipt family. reason=Employee/paid receipt, not a vendor invoice |
| MUT-AMT-1 | `evals/invoice_error_detection.py:_run_mutations` | invoice | small_amount_discrepancy | APPROVE | APPROVE | APPROVE / small_amount_discrepancy | PASS | amount +$1 is inside P-009 $300/3% |
| MUT-AMT-001 | `evals/invoice_error_detection.py:_run_mutations` | invoice | small_amount_discrepancy | APPROVE | APPROVE | APPROVE / small_amount_discrepancy | PASS | amount +$0.01 inside tolerance |
| MUT-AMT-400 | `evals/invoice_error_detection.py:_run_mutations` | invoice | material_amount_mismatch | HOLD | HOLD | HOLD / material_amount_mismatch | PASS | amount +$400 outside P-009 |
| MUT-INVNUM | `evals/invoice_error_detection.py:_run_mutations` | invoice | none | APPROVE | APPROVE | APPROVE / [] | PASS | different invoice number, same vendor/amount — legitimate similar invoice |
| MUT-PO | `evals/invoice_error_detection.py:_run_mutations` | invoice | missing_po | HOLD | HOLD | HOLD / missing_po,goods_not_received | PASS | PO number changed to missing PO |
| MUT-VENDOR-SPELL | `evals/invoice_error_detection.py:_run_mutations` | invoice | vendor_mismatch | HOLD | HOLD | HOLD / vendor_mismatch | PASS | unrelated vendor without alias precedent |
| MUT-DUP-SAME-NUM | `evals/invoice_error_detection.py:_run_mutations` | invoice | duplicate | HOLD | HOLD | HOLD / duplicate | PASS | same vendor invoice number as INV-001 |
| MUT-QTY-PO-MISS | `evals/invoice_error_detection.py:_run_mutations` | invoice | missing_po | HOLD | HOLD | HOLD / missing_po | PASS | remove PO |

## Source packs

| Pack | Location | Role |
| --- | --- | --- |
| Canonical demo company | `.cfo/data/demo/` seed 42 Maximor Demo Corp | Operational AP invoices INV-001–INV-021, ingestion emails MSG-E-*, vendor_payments |
| Demo answer keys | `.cfo/data/demo/expected_outcomes.json`, `expected_results.json`, `agent_cases.json` | Ground truth only; blocked from operational loaders |
| Generator | `.cfo/sample_data/agents/ap_ar.py` SCN-AP-001–013, SCN-ING-001–010 | Planted AP/ingestion anomalies |
| Official evaluator | `.cfo/evaluation/evaluators/ap_ar.py` AP_CASES / AP_PAYMENT | Previously accepted `not_invoice` for PO/receipt |
| Handwritten fixtures | `.cfo/data/invoices.json` | Same IDs as demo, **different** planted facts (INV-018 duplicate of Notion, etc.) |
| Inbox fixtures | `.cfo/inbox/fixtures.py` | Clean, price mismatch, no PO, quote, PO, GR, statement, payment, credit, business duplicate |
| Holdout | `.cfo/discrepancy/holdout_catalog.py` HO-AP-001–008 | Isolated discrepancy pack |
| Persistence | `.cfo/tests/test_inbox_persistence.py` | Fresh-process duplicate after restart |
| Deleted/renamed | git commit `9917178` moved `data/` → `.cfo/data/`; `tests/test_audit_adversarial.py` still exists under `.cfo/tests/` | No lost AP cases |

