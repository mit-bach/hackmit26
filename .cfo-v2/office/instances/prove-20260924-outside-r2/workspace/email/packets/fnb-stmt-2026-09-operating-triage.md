# Triage: msg-fnb-stmt-2026-09-operating-001

- message_id: msg-fnb-stmt-2026-09-operating-001
- thread_id: thr-fnb-stmt-2026-09-operating
- sender: First National Operating <notices@firstnational.example>
- subject: September 2026 statement available — Operating Account BANK-OPERATING
- source_path: workspace/world/packets/fnb-stmt-2026-09-operating.md

## Classification

- document_class: not_invoice
- subtype: bank_statement_notice
- inbox_type: BANK_NOTICE
- selected_action: NONE (no CREATE_AP_INVOICE)
- confidence: high

## Identifiers (referenced only)

- institution: First National Operating
- account: BANK-OPERATING
- period: 2026-09
- note: World left $12.40 difference unexplained; no lines marked matched

## Reason

Bank statement availability notice for the operating account. Not a vendor request for payment. Not a remittance. Not AP. Email does not own bank-rec or cash matching; do not invent match disposition. World did not mark lines matched.

## Outcome

- payable_created: false
- candidate: null
- handoff: none (not ap, not apply, not cash ownership transfer via this triage)
- packet: workspace/email/packets/fnb-stmt-2026-09-operating-triage.md
