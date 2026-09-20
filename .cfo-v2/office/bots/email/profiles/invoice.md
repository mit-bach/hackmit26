# Profile `invoice`

Display name: Email Invoice Agent.

## When

Gmail or Outlook webhook named this Bot with Profile `invoice`. Wake text names a `message_id` path.

## Do

1. Call `get_email(message_id)`. Do not invent headers or attachments.
2. For each attachment, call `get_email_attachment`. Classify each attachment.
3. If the attachment is a vendor invoice, copy Kernel-extracted fields onto `SourceAgentOutput.candidate`. Preserve email provenance (`from`, `subject`, `attachment_id`).
4. If it is a remittance or payment confirmation, `candidate` is null. Destination is `apply`.
5. If it is not an invoice, `candidate` is null. Short factual reason. No chain-of-thought dump.
6. Write the Computer path. `bot_send_prompt` to `ap` (bill) or `apply` (remittance). Await the Handle.

## Output

`SourceAgentOutput`. `source_id` is the `message_id`.
