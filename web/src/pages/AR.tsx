import { useEffect, useState } from "react";
import { get } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep } from "../components/FlowPlay";
import { AgingApplyBoard, FEATURED_PAYMENT_ID, featuredPayment } from "../components/boards/AgingApplyBoard";
import {
  AGING_BUCKETS,
  type AgingBucketKey,
  appliedInvoiceIds,
  asList,
  collectionChips,
  decisionToken,
  isRecord,
  str,
  workflowInner,
} from "../components/boards/pay-util";
import { AGING_COPY, formatAgingBucket } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const AR_STAKE = "Unmatched cash is safer than a guessed invoice.";

const AR_NODES: readonly FlowNode[] = [
  { id: "email", label: "Email", kind: "source", room: "intake", column: 0 },
  { id: "apply", label: "Apply", kind: "operator", room: "cash", column: 1 },
  { id: "ctl-cash", label: "Cash Control", kind: "verifier", room: "cash", column: 2 },
  { id: "collect", label: "Collect", kind: "operator", room: "cash", column: 1, row: 1 },
  { id: "world", label: "World", kind: "event", room: "intake", column: 2, row: 1, status: "not-attached" },
];

const AR_EDGES: readonly FlowEdge[] = [
  { id: "e-email-apply", from: "email", to: "apply", label: "remittance" },
  { id: "e-apply-ctl", from: "apply", to: "ctl-cash", label: "review" },
  { id: "e-collect-world", from: "collect", to: "world", label: "outbound", attached: false },
];

const AR_STEPS: readonly FlowStep[] = [
  { id: "remit", title: "Payment lands", nodeId: "email", manipulations: ["read memo"] },
  { id: "apply", title: "Try to apply", nodeId: "apply", manipulations: ["match invoices"] },
  { id: "control", title: "Cash control", nodeId: "ctl-cash", manipulations: ["recheck"] },
  { id: "collect", title: "Collection draft", nodeId: "collect", manipulations: ["draft follow-up"] },
];

type ArRun = "aging" | "collect" | "apply" | null;

export default function AR(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [selectedBucket, setSelectedBucket] = useState<AgingBucketKey | null>(null);
  const [lastRun, setLastRun] = useState<ArRun>(null);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/ar")
      .then((payload) => setData(payload))
      .catch(() => setData({ invoices: [], payments: [], buckets: {}, outstanding: 0 }));
  }, [result]);

  const inner = workflowInner(result);
  const applyRan = lastRun === "apply";
  const collectRan = lastRun === "collect";
  const appliedIds = applyRan ? appliedInvoiceIds(result) : [];
  const applyDecision = applyRan ? decisionToken(result) : "not run";
  const actions = collectRan ? collectionChips(result) : [];
  const payment = featuredPayment(data);
  const featured = isRecord(data) && isRecord(data.featured_payment) ? data.featured_payment : undefined;
  const remittance = featured?.payment;
  const ran = Boolean(inner?.stages || inner?.summary || inner?.result);

  async function runAging(): Promise<void> {
    setLastRun("aging");
    await run("/api/workflows/ar-aging");
  }

  async function runCollect(): Promise<void> {
    setLastRun("collect");
    await run("/api/workflows/ar-collections");
  }

  async function runApply(): Promise<void> {
    setLastRun("apply");
    await run("/api/workflows/ar-cash-apply", { payment_id: FEATURED_PAYMENT_ID });
  }

  return (
    <div className="pay-desk">
      <h1>Customer cash</h1>
      <p className="pay-stake">{AR_STAKE}</p>
      <AgingApplyBoard
        data={data}
        selectedBucket={selectedBucket}
        onSelectBucket={setSelectedBucket}
        applyRan={applyRan}
        appliedIds={appliedIds}
        applyDecision={applyDecision}
        collectRan={collectRan}
        collectionActions={actions}
      />
      <div className="pay-run">
        <RunBar
          label="Age unpaid invoices"
          running={running}
          onRun={() => {
            void runAging();
          }}
          extra={
            <>
              <button className="btn" type="button" disabled={running} onClick={() => void runCollect()}>
                Decide collection follow-up
              </button>
              <button className="btn" type="button" disabled={running} onClick={() => void runApply()}>
                Match the Lumen Labs payment
              </button>
            </>
          }
        />
        <ErrorBox error={error} />
      </div>
      <FlowPlay nodes={AR_NODES} edges={AR_EDGES} steps={AR_STEPS} mode="live" liveStages={result ?? []} />
      {ran ? <ProcessPanel stages={asList(inner?.stages)} handoffs={asList(inner?.handoffs)} summary={str(inner?.summary)} /> : null}
      <details className="pay-evidence">
        <summary>Evidence</summary>
        <p className="muted">
          {payment.payment_id} · {payment.payer_name}
        </p>
        <SourceArtifactViewer artifact={remittance} />
        <div className="pay-glossary">
          {AGING_BUCKETS.map((key) => (
            <p key={key}>
              <span className="mono">{key}</span> {formatAgingBucket(key)} — {AGING_COPY[key]}
            </p>
          ))}
        </div>
      </details>
    </div>
  );
}
