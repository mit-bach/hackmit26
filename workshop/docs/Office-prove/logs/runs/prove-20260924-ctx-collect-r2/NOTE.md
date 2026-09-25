# prove-20260924-ctx-collect-r2

Context module check, then the collections situation. Port 8801. Golden stayed `golden-20260920-r1`.

Wake (no tool id):

```
profile: chase
Maximor Demo Corp, September 2026. Customer invoices are still open. You own collections. Work the aging. Do not apply their cash. Do not close the month. Do not ask a person.
```

- `context/manifest.jsonl` has one record. Office text has the roster and does not say “Keep messages short.”
- `context/bot-7174e82427d07297.txt` contains the collect `BOT.md` and `Active profile chase`.
- First Pi tool was `memory_read`, not a read of `BOT.md`.
- Kernel: `get_collection_candidates` once, `get_ar_customer` eight times, `send_office_outbound` ten times, `reply_in_thread` ten times. Handle `h_63618026-1f83-4405-9838-e05ab207922e` completed.
- Pair-thread replies in protocol: 2. Mailbox replies exist. The pair thread is still short of several back-and-forths on one invoice.
