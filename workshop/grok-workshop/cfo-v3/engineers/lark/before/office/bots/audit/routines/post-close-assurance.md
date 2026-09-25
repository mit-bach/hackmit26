# Routine `post-close-assurance`

Owning Bot: `audit`.
Profile: `interpret`.
Cadence: monthly.
Conversation: `room:books-close`.
`approvalLevel`: never.

## Prompt (wake text)

```
profile: interpret
Run after-the-fact assurance on this period's close pack.
Pack path is named in this Wake. Call bot_get_agent_transcript_tail for the protocol tail.
Python samples and re-performs. Interpret Kernel finding IDs only.
Write under workspace/audit/ and runs/audit/. Path lease before each write.
Then bot_send_prompt to audit with profile: report. Await the Handle.
Do not ask a human. Do not load the audit answer key. Do not fix the books. Sample vendors, payments, journals, invoices, payroll, and bank deposit accounts.
Do not concur for ctl-*. Do not approve a pay-run.
```

Session 00 lands this Routine on `office/computer/harness/roster.json`. Kernel wake body: `office/bots/audit/host.py` `run_assurance_host`.
