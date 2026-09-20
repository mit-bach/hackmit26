import { useEffect, useRef, useState } from "react";
import { get } from "../api";
import { BeforeAfterDiff, ProcessPanel, ProvenanceLinks, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep } from "../components/FlowPlay";
import { MatchBoard, DEFAULT_AP_ID } from "../components/boards/MatchBoard";
import { asList, decisionToken, isRecord, str, workflowInner } from "../components/boards/pay-util";
import { formatException, formatFieldKey } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const AP_STAKE = "A bill is paid only if it matches the order and the receipt.";

const AP_NODES: readonly FlowNode[] = [
  { id: "email", label: "Email", kind: "source", room: "intake", column: 0 },
  { id: "ap", label: "AP", kind: "operator", room: "pay", column: 1 },
  { id: "ctl-pay", label: "Payables Control", kind: "verifier", room: "pay", column: 2 },
  { id: "pay", label: "Payments", kind: "operator", room: "pay", column: 3 },
];

const AP_EDGES: readonly FlowEdge[] = [
  { id: "e-email-ap", from: "email", to: "ap", label: "bill" },
  { id: "e-ap-ctl", from: "ap", to: "ctl-pay", label: "match" },
  { id: "e-ctl-pay", from: "ctl-pay", to: "pay", label: "schedule" },
];

const AP_STEPS: readonly FlowStep[] = [
  { id: "land", title: "Bill lands", nodeId: "email", manipulations: ["classify"] },
  { id: "match", title: "Three-way match", nodeId: "ap", manipulations: ["match"] },
  { id: "control", title: "Payables control", nodeId: "ctl-pay", manipulations: ["recheck"] },
  { id: "schedule", title: "Payment draft", nodeId: "pay", manipulations: ["schedule"] },
];

function exceptionList(detail: unknown, result: unknown): readonly string[] {
  const inner = workflowInner(result);
  const fromInner = isRecord(inner?.evidence) ? asList(inner.evidence.exception_types) : [];
  const fromDetail = isRecord(detail) ? asList(detail.exceptions) : [];
  const source = fromInner.length ? fromInner : fromDetail;
  return source.map((item) => str(item)).filter((item): item is string => Boolean(item));
}

export default function AP(): JSX.Element {
  const [rows, setRows] = useState<unknown[]>([]);
  const [detail, setDetail] = useState<unknown>(null);
  const [selectedId, setSelectedId] = useState(DEFAULT_AP_ID);
  const requestedId = useRef(DEFAULT_AP_ID);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get<{ invoices?: unknown[] }>("/api/invoices")
      .then((payload) => setRows(payload.invoices || []))
      .catch(() => setRows([]));
  }, [result]);

  async function open(id: string): Promise<void> {
    requestedId.current = id;
    setSelectedId(id);
    try {
      const row = await get(`/api/invoices/${id}`);
      if (requestedId.current === id) {
        setDetail(row);
      }
    } catch {
      if (requestedId.current === id) {
        setDetail(null);
      }
    }
  }

  useEffect(() => {
    void open(DEFAULT_AP_ID);
  }, []);

  const inner = workflowInner(result);
  const io = isRecord(inner?.io) ? inner.io : undefined;
  const decision = decisionToken(result, isRecord(detail) ? str(detail.match_status) : undefined);
  const exceptions = exceptionList(detail, result);
  const ran = Boolean(inner?.stages);
  const sourceEmails = isRecord(detail) ? asList(detail.source_emails) : [];
  const threeWay = isRecord(detail) && isRecord(detail.three_way) ? detail.three_way : undefined;
  const artifacts = isRecord(threeWay?.artifacts) ? threeWay.artifacts : {};
  const pair = isRecord(detail) && isRecord(detail.duplicate_peer) ? detail.duplicate_peer : undefined;

  return (
    <div className="pay-desk">
      <h1>Vendor bills</h1>
      <p className="pay-stake">{AP_STAKE}</p>
      <MatchBoard rows={rows} selectedId={selectedId} detail={detail} decision={decision} onSelect={open} />
      <div className="pay-run">
        <RunBar
          label="Check this vendor bill"
          running={running}
          onRun={() => run(`/api/workflows/ap/${selectedId}`)}
          extra={
            <button className="btn" type="button" disabled={running} onClick={() => run("/api/workflows/schedule")}>
              Draft this week's payments
            </button>
          }
        />
        <ErrorBox error={error} />
      </div>
      <FlowPlay nodes={AP_NODES} edges={AP_EDGES} steps={AP_STEPS} mode="live" liveStages={result ?? []} />
      {ran ? <ProcessPanel stages={asList(inner?.stages)} handoffs={asList(inner?.handoffs)} summary={str(inner?.summary)} /> : null}
      <details className="pay-evidence">
        <summary>Evidence</summary>
        {exceptions.map((item) => (
          <p key={item}>{formatException(item)}</p>
        ))}
        {pair ? (
          <>
            <SourceArtifactViewer artifact={pair.document_a} />
            <SourceArtifactViewer artifact={pair.document_b} />
          </>
        ) : (
          <>
            {sourceEmails.map((item, index) => (
              <SourceArtifactViewer key={str(isRecord(item) ? item.artifact_id : undefined) || String(index)} artifact={item} />
            ))}
            <SourceArtifactViewer artifact={artifacts.invoice || (isRecord(detail) ? detail.source_document : undefined)} />
            <SourceArtifactViewer artifact={artifacts.purchase_order} compact />
            <SourceArtifactViewer artifact={artifacts.goods_receipt} compact />
          </>
        )}
        {io?.before || io?.after ? (
          <BeforeAfterDiff
            before={io.before}
            after={io.after}
            fields={["invoice_id", "match_status", "duplicate_status", "payment_state", "accounting_status", "exceptions", "linked_payments", "linked_journals"]}
            labelFor={formatFieldKey}
          />
        ) : null}
        <ProvenanceLinks links={isRecord(detail) ? (detail.provenance as unknown[]) : undefined} />
      </details>
    </div>
  );
}
