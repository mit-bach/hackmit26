import { useEffect, useState } from "react";
import { get, usd, statusTone } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill, RunBar } from "../layout/Shell";
import { BeforeAfterDiff, DemoLayout, OutputHeadline, ProcessPanel, ProvenanceLinks, SourceArtifactViewer } from "../components/Demo";
import { Definition, LineageChain, TraceIds, WhatsHappening } from "../components/Explain";
import { formatDecision, formatException, formatFieldKey, formatStatus } from "../copy";

export default function AP() {
  const [rows, setRows] = useState<any[]>([]);
  const [detail, setDetail] = useState<any>(null);
  const { running, result, error, run } = useWorkflow();
  const selected = detail?.invoice_id || "INV-003";

  useEffect(() => {
    get<{ invoices: any[] }>("/api/invoices").then((payload) => setRows(payload.invoices || []));
  }, [result]);

  async function open(id: string) {
    const row = await get(`/api/invoices/${id}`);
    setDetail(row);
  }

  useEffect(() => {
    open("INV-003");
  }, []);

  const inner = result?.result;
  const tw = detail?.three_way?.artifacts || {};
  const io = inner?.io;
  const pair = detail?.duplicate_peer;

  return (
    <DemoLayout
      eyebrow="Accounts payable"
      title="Vendor bills waiting to be paid"
      task="Accounts payable is money the company owes vendors. Maximor checks each bill against the purchase order and the record that goods or services were received before it can go on a payment run."
      happening={
        <WhatsHappening
          happening="A vendor bill is only safe to pay if it matches what was ordered and what actually arrived. Maximor also looks for a second copy of the same bill."
          figureOut="Should this vendor invoice be approved, or held because something does not line up?"
          why="Paying a duplicate or an unauthorized bill would send company cash to the wrong place."
        />
      }
      runBar={
        <>
          <RunBar
            label={`Run AP on ${selected}`}
            running={running}
            onRun={() => run(`/api/workflows/ap/${selected}`)}
            extra={
              <button className="btn" disabled={running} onClick={() => run("/api/workflows/schedule")}>
                Run payment schedule
              </button>
            }
          />
          <ErrorBox error={error} />
          <div className="card" style={{ marginBottom: 14 }}>
            <h2>Invoice register</h2>
            <table className="data">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th className="right">Amount</th>
                  <th>Match</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.invoice_id} className={row.invoice_id === selected ? "selected" : ""} onClick={() => open(row.invoice_id)}>
                    <td>
                      <div>{row.vendor}</div>
                      <TraceIds ids={[row.invoice_id, row.po_id]} />
                    </td>
                    <td className="num right">{usd(row.amount)}</td>
                    <td>
                      <Pill tone={statusTone(row.duplicate_status === "duplicate" ? "duplicate" : row.match_status)}>
                        {row.duplicate_status === "duplicate" ? formatStatus("duplicate") : formatStatus(row.match_status)}
                      </Pill>
                    </td>
                    <td>{formatStatus(row.payment_state)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      }
      input={
        pair?.document_a ? (
          <div className="stack">
            <div className="card">
              <h2>Input document A</h2>
              <SourceArtifactViewer artifact={pair.document_a} />
            </div>
            <div className="card">
              <h2>Input document B</h2>
              <SourceArtifactViewer artifact={pair.document_b} />
            </div>
          </div>
        ) : (
          <div className="stack">
            <div className="card">
              <h2>Invoice</h2>
              {(detail?.source_emails || []).map((item: any) => (
                <SourceArtifactViewer key={item.artifact_id} artifact={item} />
              ))}
              {!(detail?.source_emails || []).length ? <SourceArtifactViewer artifact={tw.invoice || detail?.source_document} /> : null}
            </div>
            <div className="match-trio">
              <div className="card">
                <h2>Invoice</h2>
                <div className="mono">{tw.invoice?.record?.invoice_id || detail?.invoice_id}</div>
                <div>{usd(tw.invoice?.record?.amount || detail?.amount)}</div>
              </div>
              <div className="card">
                <h2>Purchase order</h2>
                <SourceArtifactViewer artifact={tw.purchase_order} compact />
              </div>
              <div className="card">
                <h2>Goods receipt</h2>
                <SourceArtifactViewer artifact={tw.goods_receipt} compact />
              </div>
            </div>
          </div>
        )
      }
      process={<ProcessPanel stages={inner?.stages} handoffs={inner?.handoffs} summary={inner?.summary} />}
      output={
        <div className="stack">
          <div className="card">
            <OutputHeadline label="Payables decision" value={formatDecision(inner?.decision?.decision || detail?.match_status || "not run")} />
            <Definition term="Three-way match" />
            {pair?.comparison ? (
              <table className="data">
                <thead>
                  <tr>
                    <th>What was compared</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(pair.comparison)
                    .filter(([key]) => key.endsWith("_match"))
                    .map(([key, value]) => (
                      <tr key={key}>
                        <td>{formatFieldKey(key.replace("_match", ""))}</td>
                        <td>{String(value) === "true" ? "Agrees" : String(value) === "false" ? "Does not agree" : formatStatus(value)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : null}
            <dl className="kv">
              <dt>Duplicate check</dt>
              <dd>{formatStatus(detail?.duplicate_status)}</dd>
              <dt>Problems found</dt>
              <dd>{(detail?.exceptions || inner?.evidence?.exception_types || []).map(formatException).join("; ") || "None"}</dd>
              <dt>Payment</dt>
              <dd>{formatStatus(detail?.payment_state)}</dd>
            </dl>
            <p>{inner?.explanation?.narrative || inner?.io?.explanation || "Run AP to see the English decision."}</p>
            {inner?.naive ? <p>{inner.naive}</p> : null}
            <LineageChain steps={inner?.lineage?.steps} />
            {(inner?.lineage?.changed || []).map((item: string) => (
              <p key={item}>{item}</p>
            ))}
            <ProvenanceLinks links={detail?.provenance} />
          </div>
          {io?.before || io?.after ? (
            <div className="card">
              <h2>Before / after</h2>
              <BeforeAfterDiff before={io.before} after={io.after} fields={["invoice_id", "match_status", "duplicate_status", "payment_state", "accounting_status", "exceptions", "linked_payments", "linked_journals"]} labelFor={formatFieldKey} />
            </div>
          ) : null}
        </div>
      }
    />
  );
}
