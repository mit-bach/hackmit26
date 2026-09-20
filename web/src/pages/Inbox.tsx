import { useEffect, useState } from "react";
import { get, usd } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill, RunBar } from "../layout/Shell";
import { DemoLayout, OutputHeadline, ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { ResultBlock, WhatsHappening } from "../components/Explain";
import { formatStatus } from "../copy";

export default function Inbox() {
  const [catalog, setCatalog] = useState<any>(null);
  const [selected, setSelected] = useState<string>("MSG-E-MESSY");
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/inbox").then(setCatalog);
  }, [result]);

  const source = catalog?.sample_artifacts?.[selected] || (catalog?.emails || []).find((item: any) => item.message_id === selected);
  const inner = result?.result;
  const io = inner?.io;
  const outputs = io?.outputs;
  const attachments = source?.attachments || source?.email?.attachments || [];

  return (
    <DemoLayout
      eyebrow="Inbox"
      title="What just arrived in finance email?"
      task="Maximor reads incoming finance emails and attachments and decides whether they are invoices, quotes, receipts, or something else — before anyone books a bill."
      happening={
        <WhatsHappening
          happening="Vendors send many kinds of documents. A quote looks like a bill, a statement lists old invoices, and a receipt is proof of a purchase already made. Maximor has to classify first."
          figureOut="Is this document a vendor invoice Maximor should put on the books?"
          why="Treating a quote as a bill would create a fake amount owed."
        />
      }
      runBar={
        <>
          <RunBar
            label="Identify this document"
            running={running}
            onRun={() => run("/api/workflows/invoice-ingestion", { sample_id: selected })}
            extra={
              <button className="btn" disabled={running} onClick={() => run("/api/workflows/inbox", {})}>
                Sort the inbox
              </button>
            }
          />
          <ErrorBox error={error} />
          <div className="card" style={{ marginBottom: 14 }}>
            <h2>Documents to try</h2>
            <table className="data">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>What it looks like</th>
                </tr>
              </thead>
              <tbody>
                {(catalog?.samples || []).map((item: any) => (
                  <tr key={item.sample_id} className={item.sample_id === selected ? "selected" : ""} onClick={() => setSelected(item.sample_id)}>
                    <td>{item.subject}</td>
                    <td>
                      <Pill>{formatStatus(item.kind)}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      }
      input={
        <div className="stack">
          <div className="card">
            <SourceArtifactViewer artifact={source?.kind ? source : source ? { kind: "email", artifact_id: source.message_id, title: source.subject, source_path: "ingestion/emails.json", record: source, email: source } : null} />
          </div>
          {attachments.map((att: any) => (
            <div className="card" key={att.artifact_id || att.attachment_id || att.filename}>
              <SourceArtifactViewer artifact={att.kind ? att : { kind: "document", ...att, record: att }} />
            </div>
          ))}
        </div>
      }
      process={<ProcessPanel stages={inner?.stages} handoffs={inner?.handoffs} summary={inner?.summary} />}
      output={
        inner ? (
          <div className="card">
            <OutputHeadline label="Is this a vendor invoice?" value={formatStatus(outputs?.is_invoice ? "invoice" : outputs?.classification || inner.classification)} />
            <ResultBlock
              found={
                outputs?.is_invoice || inner.classification === "invoice"
                  ? "The Email Agent identified this as a vendor invoice and extracted the fields needed to book a bill."
                  : `The Email Agent identified this as ${formatStatus(outputs?.classification || inner.classification).toLowerCase()}, not a vendor bill to pay.`
              }
              why={inner.classification_reason || "A quote, statement, or receipt should not create money the company owes."}
              result={
                (inner.record_ids || []).length
                  ? "A vendor bill was created from this document and handed to Accounts Payable."
                  : "No vendor bill was created. Treating this as a bill would invent an amount the company does not owe."
              }
            />
            <dl className="kv">
              <dt>Document type</dt>
              <dd>
                <Pill>{formatStatus(outputs?.classification || inner.classification)}</Pill>
              </dd>
              <dt>Vendor</dt>
              <dd>{inner.extracted?.vendor || "—"}</dd>
              <dt>Invoice number</dt>
              <dd>{inner.extracted?.invoice_number || "—"}</dd>
              <dt>Amount</dt>
              <dd>{inner.extracted?.amount != null && inner.extracted?.amount !== "—" ? usd(Number(inner.extracted.amount)) : "—"}</dd>
              <dt>Purchase order</dt>
              <dd className="mono">{inner.extracted?.po_number || "—"}</dd>
            </dl>
            {(outputs?.canonical_invoices || []).map((item: any) => (
              <SourceArtifactViewer key={item.artifact_id} artifact={item} compact />
            ))}
          </div>
        ) : (
          <div className="card">
            <p className="muted">Run this document through intake to see whether Maximor treats it as a vendor bill, and what it extracts.</p>
          </div>
        )
      }
    />
  );
}
