import { ReactNode, useState } from "react";
import { Link } from "react-router-dom";
import { usd, statusTone } from "../api";
import { formatAgent, formatFieldKey, formatHandoff, formatRecordType, formatStage, formatStatus } from "../copy";
import { Pill, Stages } from "../layout/Shell";

export function DemoLayout({
  eyebrow,
  title,
  task,
  happening,
  input,
  output,
  process,
  extra,
  runBar,
}: {
  eyebrow: string;
  title: string;
  task: string;
  happening?: ReactNode;
  input: ReactNode;
  output: ReactNode;
  process?: ReactNode;
  extra?: ReactNode;
  runBar?: ReactNode;
}) {
  return (
    <div className="demo-page">
      <div className="page-head">
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p className="lede">{task}</p>
      </div>
      {happening}
      {runBar}
      <div className="io-flow" aria-label="Original input to final output">
        <div className="io-col input-col">
          <div className="io-label">Original input</div>
          {input}
        </div>
        <div className="io-arrow" aria-hidden>
          →
        </div>
        <div className="io-col process-col">
          <div className="io-label">System process</div>
          {process || <p className="muted">Run the workflow to see agent steps.</p>}
        </div>
        <div className="io-arrow" aria-hidden>
          →
        </div>
        <div className="io-col output-col">
          <div className="io-label">Final output</div>
          {output}
        </div>
      </div>
      {extra}
    </div>
  );
}

export function ProvenanceLinks({ links }: { links?: any[] }) {
  if (!links?.length) return null;
  return (
    <div className="provenance">
      {links.filter(Boolean).map((link, idx) => {
        const id = typeof link === "string" ? link : link.id;
        const kind = typeof link === "string" ? "" : link.kind;
        const href = hrefFor(id, kind);
        return (
          <span key={`${id}-${idx}`}>
            {idx > 0 ? <span className="muted"> → </span> : null}
            {href ? (
              <Link className="mono" to={href}>
                {id}
              </Link>
            ) : (
              <span className="mono">{id}</span>
            )}
          </span>
        );
      })}
    </div>
  );
}

function hrefFor(id?: string, kind?: string): string | null {
  if (!id) return null;
  if (kind === "email" || String(id).startsWith("MSG-")) return "/inbox";
  if (String(id).startsWith("INV-AR") || kind === "customer_invoice") return "/ar";
  if (String(id).startsWith("INV-") || kind === "invoice" || kind === "purchase_order" || kind === "goods_receipt") return "/ap";
  if (String(id).startsWith("TXN-") || kind === "bank_transaction" || kind === "ledger_entry") return "/cash";
  if (String(id).startsWith("po_") || kind === "stripe_payout") return "/stripe";
  if (String(id).startsWith("JE-") || String(id).startsWith("TASK-") || String(id).startsWith("ACC-")) return "/close";
  if (String(id).startsWith("MEM-") || kind === "decision_memory") return "/memory";
  return null;
}

export function FriendlyRaw({
  friendly,
  raw,
  defaultTab = "friendly",
  friendlyLabel = "Explanation",
  rawLabel = "Developer details",
}: {
  friendly: ReactNode;
  raw: unknown;
  defaultTab?: "friendly" | "raw";
  friendlyLabel?: string;
  rawLabel?: string;
}) {
  const [tab, setTab] = useState(defaultTab);
  return (
    <div>
      <div className="tabs">
        <button className={tab === "friendly" ? "tab on" : "tab"} onClick={() => setTab("friendly")}>
          {friendlyLabel}
        </button>
        <button className={tab === "raw" ? "tab on" : "tab"} onClick={() => setTab("raw")}>
          {rawLabel}
        </button>
      </div>
      {tab === "friendly" ? friendly : <pre className="raw-json">{JSON.stringify(raw, null, 2)}</pre>}
    </div>
  );
}

export function BeforeAfterDiff({
  before,
  after,
  fields,
  onlyChanged = false,
  unchangedMessage,
  labelFor,
}: {
  before?: Record<string, unknown> | null;
  after?: Record<string, unknown> | null;
  fields?: string[];
  onlyChanged?: boolean;
  unchangedMessage?: string;
  labelFor?: (key: string) => string;
}) {
  if (!before && !after) return <p className="muted">No persisted before/after snapshot yet.</p>;
  const keys = fields || Array.from(new Set([...Object.keys(before || {}), ...Object.keys(after || {})]));
  const rows = keys.map((key) => {
    const left = formatValue((before || {})[key], key);
    const right = formatValue((after || {})[key], key);
    return { key, left, right, changed: left !== right };
  });
  const visible = onlyChanged ? rows.filter((row) => row.changed) : rows;
  if (onlyChanged && visible.length === 0) {
    return <p className="muted">{unchangedMessage || "Nothing changed between the earlier and later values."}</p>;
  }
  return (
    <div className="table-scroll">
      <table className="data diff">
        <thead>
          <tr>
            <th>What</th>
            <th>Before</th>
            <th>After</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((row) => (
            <tr key={row.key} className={row.changed ? "changed" : ""}>
              <td>{labelFor ? labelFor(row.key) : row.key}</td>
              <td>{row.left}</td>
              <td>{row.right}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(value: unknown, key?: string): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    if (key && (key.endsWith("_minor") || key.includes("cents"))) return usd(value / 100);
    if (key && /cash|amount|outstanding|payment|inflow|outflow|payroll|expense/.test(key)) return usd(value);
    return String(value);
  }
  if (Array.isArray(value)) return value.length ? value.map((item) => (typeof item === "object" ? formatStatus(item) : formatStatus(item))).join(", ") : "—";
  if (typeof value === "object") return formatStatus(value);
  return formatStatus(value);
}

export function ProcessPanel({ stages, handoffs, summary }: { stages?: any[]; handoffs?: any[]; summary?: string }) {
  const translated = (stages || []).map((stage) => {
    const copy = formatStage(stage);
    return { ...stage, label: copy.label, detail: copy.detail || stage.detail };
  });
  return (
    <div className="card process-card">
      {summary ? <div className="muted" style={{ marginBottom: 8 }}>{summary}</div> : null}
      <Stages stages={translated} />
      {handoffs?.length ? (
        <div className="handoff-list">
          {handoffs.map((item: any, idx: number) => (
            <p key={idx} className="muted">
              {typeof item === "string"
                ? formatHandoff([item])
                : formatHandoff(item.bots || [item.slug || item.display_name], item.workflow)}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function OutputHeadline({ label, value, tone }: { label: string; value: ReactNode; tone?: string }) {
  return (
    <div className="output-headline">
      <div className="muted">{label}</div>
      <div>
        <Pill tone={tone || statusTone(String(value))}>{value}</Pill>
      </div>
    </div>
  );
}

export function Kv({ rows }: { rows: Array<[string, ReactNode]> }) {
  return (
    <dl className="kv">
      {rows.map(([key, value]) => (
        <div key={key} className="kv-row">
          <dt>{key}</dt>
          <dd>{value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SourceArtifactViewer({ artifact, compact = false }: { artifact: any; compact?: boolean }) {
  if (!artifact) return <p className="muted">No source artifact on file for this record.</p>;
  const kind = artifact.kind || artifact.record?.kind;
  const record = artifact.record ?? artifact;
  return (
    <div className={`artifact ${compact ? "compact" : ""}`}>
      <div className="split">
        <strong>{artifact.title || artifact.artifact_id || kind}</strong>
        <span className="mono muted">{artifact.artifact_id}</span>
      </div>
      <div className="muted" style={{ marginBottom: 8 }}>
        {formatRecordLabel(kind)} {artifact.source_path ? <span className="mono">· {artifact.source_path}</span> : null}
      </div>
      <FriendlyRaw
        raw={record}
        friendly={
          <>
            {renderFriendly(kind, artifact, record)}
            <ProvenanceLinks links={artifact.provenance} />
          </>
        }
      />
    </div>
  );
}

function renderFriendly(kind: string, artifact: any, record: any) {
  if (kind === "email" || artifact.email) return <EmailView email={artifact.email || record} attachments={artifact.attachments || artifact.email?.attachments} />;
  if (kind === "document") return <DocumentView filename={artifact.filename || record.filename} contentType={artifact.content_type || record.content_type} text={artifact.text ?? record.text} />;
  if (kind === "invoice") return <InvoiceView invoice={record} emails={artifact.source_emails} />;
  if (kind === "purchase_order") return <PoView po={record} />;
  if (kind === "goods_receipt") return <GrView gr={record} />;
  if (kind === "bank_transaction" || kind === "ledger_entry") {
    return (
      <dl className="kv">
        <dt>ID</dt>
        <dd className="mono">{record.transaction_id || record.entry_id}</dd>
        <dt>Date</dt>
        <dd>{record.date}</dd>
        <dt>Amount</dt>
        <dd>{usd(record.amount)}</dd>
        <dt>Description</dt>
        <dd>{record.description}</dd>
        <dt>Counterparty</dt>
        <dd>{record.counterparty}</dd>
        <dt>Reference</dt>
        <dd className="mono">{record.reference || "—"}</dd>
      </dl>
    );
  }
  if (kind === "stripe_payout" || kind === "stripe_balance_txn") {
    const cents = record.amount;
    return (
      <dl className="kv">
        <dt>ID</dt>
        <dd className="mono">{record.payout_id || record.id}</dd>
        <dt>Type</dt>
        <dd>{record.type || record.source_event_type || kind}</dd>
        <dt>Amount (minor)</dt>
        <dd>{cents}</dd>
        <dt>Amount</dt>
        <dd>{typeof cents === "number" ? usd(cents / 100) : "—"}</dd>
        <dt>Payout</dt>
        <dd className="mono">{record.payout_id || record.payout}</dd>
        <dt>Bank deposit</dt>
        <dd>{record.bank_deposit_id} {record.bank_deposit_amount != null ? usd(record.bank_deposit_amount) : ""}</dd>
      </dl>
    );
  }
  if (kind === "journal_entry") return <JournalView row={record} />;
  if (kind === "table") return <TableView columns={artifact.columns} rows={artifact.rows || record} />;
  return <RowView row={record} />;
}

function EmailView({ email, attachments }: { email: any; attachments?: any[] }) {
  if (!email) return null;
  return (
    <div>
      <dl className="kv">
        <dt>From</dt>
        <dd>{email.from}</dd>
        <dt>To</dt>
        <dd>{email.to}</dd>
        <dt>Subject</dt>
        <dd>{email.subject}</dd>
        <dt>Timestamp</dt>
        <dd>{email.sent_at}</dd>
      </dl>
      <div className="doc-paper">
        <pre>{email.body}</pre>
      </div>
      {(attachments || email.attachments || []).map((att: any) => (
        <DocumentView
          key={att.artifact_id || att.attachment_id || att.filename}
          filename={att.filename || att.title}
          contentType={att.content_type || att.record?.content_type}
          text={att.text || att.record?.text}
        />
      ))}
    </div>
  );
}

function DocumentView({ filename, contentType, text }: { filename?: string; contentType?: string; text?: string }) {
  const isPdf = (contentType || "").includes("pdf") || String(filename || "").toLowerCase().endsWith(".pdf");
  const isImage = (contentType || "").startsWith("image/");
  return (
    <div className="doc-wrap">
      <div className="split">
        <span className="mono">{filename || "document"}</span>
        <span className="muted">{contentType || (isPdf ? "application/pdf" : "text")}</span>
      </div>
      {isImage && text?.startsWith("data:") ? <img src={text} alt={filename || "source"} className="doc-image" /> : <div className={`doc-paper ${isPdf ? "pdf" : ""}`}><pre>{text || "(empty)"}</pre></div>}
    </div>
  );
}

function InvoiceView({ invoice, emails }: { invoice: any; emails?: any[] }) {
  if (!invoice) return null;
  return (
    <div>
      {emails?.length ? emails.map((item) => <SourceArtifactViewer key={item.artifact_id} artifact={item} compact />) : null}
      <dl className="kv">
        <dt>Invoice</dt>
        <dd className="mono">{invoice.invoice_id}</dd>
        <dt>Vendor</dt>
        <dd>{invoice.vendor}</dd>
        <dt>Vendor invoice #</dt>
        <dd>{invoice.vendor_invoice_number}</dd>
        <dt>Date</dt>
        <dd>{invoice.invoice_date}</dd>
        <dt>Due</dt>
        <dd>{invoice.due_date}</dd>
        <dt>Amount</dt>
        <dd>{usd(invoice.amount)}</dd>
        <dt>PO</dt>
        <dd className="mono">{invoice.po_id || "—"}</dd>
        <dt>Description</dt>
        <dd>{invoice.description}</dd>
      </dl>
    </div>
  );
}

function PoView({ po }: { po: any }) {
  return (
    <dl className="kv">
      <dt>PO</dt>
      <dd className="mono">{po.po_id}</dd>
      <dt>Vendor</dt>
      <dd>{po.vendor}</dd>
      <dt>Authorized</dt>
      <dd>{usd(po.authorized_amount)}</dd>
      <dt>Status</dt>
      <dd>{po.status}</dd>
      <dt>Approver</dt>
      <dd>{po.approver}</dd>
      <dt>Description</dt>
      <dd>{po.description}</dd>
    </dl>
  );
}

function GrView({ gr }: { gr: any }) {
  return (
    <dl className="kv">
      <dt>Receipt</dt>
      <dd className="mono">{gr.receipt_id}</dd>
      <dt>PO</dt>
      <dd className="mono">{gr.po_id}</dd>
      <dt>Received</dt>
      <dd>{String(gr.received)}</dd>
      <dt>Qty ordered</dt>
      <dd>{gr.quantity_ordered}</dd>
      <dt>Qty received</dt>
      <dd>{gr.quantity_received}</dd>
      <dt>Amount received</dt>
      <dd>{usd(gr.amount_received)}</dd>
    </dl>
  );
}

function JournalView({ row }: { row: any }) {
  const amount = row.amount ?? (row.amount_minor != null ? row.amount_minor / 100 : null);
  return (
    <dl className="kv">
      <dt>Entry</dt>
      <dd className="mono">{row.entry_id}</dd>
      <dt>Debit</dt>
      <dd>{row.debit_account || row.account}</dd>
      <dt>Credit</dt>
      <dd>{row.credit_account || "—"}</dd>
      <dt>Amount</dt>
      <dd>{usd(amount)}</dd>
      <dt>Memo</dt>
      <dd>{row.memo || row.description}</dd>
      <dt>Source</dt>
      <dd className="mono">{row.source_document_id || (row.related_ids || []).join(", ") || "—"}</dd>
    </dl>
  );
}

function RowView({ row }: { row: any }) {
  if (!row || typeof row !== "object") return <pre className="raw-json">{String(row)}</pre>;
  const entries = Object.entries(row).filter(([key]) => key !== "raw_metadata" && key !== "lines" && key !== "attachments");
  return (
    <dl className="kv">
      {entries.slice(0, 14).map(([key, value]) => (
        <div key={key} className="kv-row">
          <dt>{key}</dt>
          <dd className="mono">{formatValue(value, key)}</dd>
        </div>
      ))}
    </dl>
  );
}

function TableView({ columns, rows }: { columns?: string[]; rows?: any[] }) {
  if (!rows?.length) return <p className="muted">No rows.</p>;
  const cols = columns?.length ? columns : Object.keys(rows[0] || {});
  return (
    <div className="table-scroll">
      <table className="data">
        <thead>
          <tr>
            {cols.map((col) => (
              <th key={col}>{formatFieldKey(col)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.invoice_id || row.week_start || idx}>
              {cols.map((col) => (
                <td key={col} className={typeof row[col] === "number" ? "num right" : ""}>
                  {typeof row[col] === "number" && /cash|amount|expense|authorized|payment|inflow|outflow|payroll/.test(col)
                    ? usd(row[col])
                    : formatValue(row[col], col)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ArtifactStack({ artifacts }: { artifacts?: any[] }) {
  if (!artifacts?.length) return <p className="muted">No original input loaded.</p>;
  return (
    <div className="stack">
      {artifacts.filter(Boolean).map((item, idx) => (
        <div className="card" key={item.artifact_id || idx}>
          <SourceArtifactViewer artifact={item} />
        </div>
      ))}
    </div>
  );
}

function formatRecordLabel(kind?: string) {
  return formatRecordType(kind);
}

export function flattenInputs(value: any): any[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.flatMap(flattenInputs);
  if (value.artifact_id || value.kind) return [value];
  if (typeof value !== "object") return [];
  const nested: any[] = [];
  for (const item of Object.values(value)) {
    nested.push(...flattenInputs(item));
  }
  return nested;
}
