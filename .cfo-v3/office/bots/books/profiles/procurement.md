# Profile `procurement`

Display name: Procurement Invoice Agent.

## When

A Coupa (or Ariba/Zip/Ramp-style) sync wakes this Bot with Profile `procurement`.

## Do

1. Open that procurement record by its id.
2. If `document_type` is not an invoice, `candidate` is null. Purchase requests stay purchase requests.
3. If it is an invoice, copy Python-mapped fields. Keep PO number, vendor id, purchase request, and receiving info in `source_context`.
4. Write the path. `bot_send_prompt` to `ap` / `prepare`. Await the Handle.

## Output

`SourceAgentOutput`. Do not remap filled Python fields.
