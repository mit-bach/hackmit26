# Office demo walkthrough

Seeded without live email. Kernel traces and the Stripe pack are on this Computer.

- Computer: `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer`
- Inbox handoffs: 2
- Pay pool: INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-011, INV-012, INV-017, ING-001
- Stripe pack: `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer/data/simulations/stripe`

## What to show

- Open Email. Set Transcript detail to Full. Ask it to call list_email_candidates for 2026-09.
- Open AP. Ask it to load invoice ING-001 with tools.get_invoice (demo-inbox already landed it).
- Inspector → Pi events / Pi RPC shows the live Harness stream, not a mascot-only status.
- There is no live mailbox. demo-inbox wrote traces under computer/runs/inbox.
- Stripe objects live under computer/data/simulations/stripe (symlink to .cfo/data).

## Inbox seed

```
Finance Inbox Demo

[1] MSG-INBOX-001
Sender: Counterparty Message Agent  run=RUN-CP-MSG-INBOX-001  sent MSG-INBOX-001
Receiver: Finance Inbox Agent  run=RUN-IB-MSG-INBOX-001
Classification: VENDOR_INVOICE  action=CREATE_AP_INVOICE
Extracted: invoice=ACM-INBOX-1001, vendor=Acme Supplies, amount_cents=1245000, po=PO-101
Duplicate/validation: none  errors=[]
Canonical invoice: ING-001
Three-way match: MATCHED  exceptions=[]
Final status: CREATED  reasons=['AP_INVOICE_CREATED']
Trace: /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer/runs/inbox/traces/INBOX-MSG-INBOX-001.json

[2] MSG-INBOX-010
Sender: Counterparty Message Agent  run=RUN-CP-MSG-INBOX-010  sent MSG-INBOX-010
Receiver: Finance Inbox Agent  run=RUN-IB-MSG-INBOX-010
Classification: NON_FINANCE  action=IGNORE
Extracted: vendor=People Ops
Duplicate/validation: none  errors=[]
Canonical invoice: (none)
Three-way match: n/a  exceptions=[]
Final status: IGNORED  reasons=['IGNORED']
Trace: /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v2/office/computer/runs/inbox/traces/INBOX-MSG-INBOX-010.json

Inbox-created AP invoices: ING-001
```
