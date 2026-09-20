import { useEffect, useState } from "react";
import { get, usd } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep, type LiveStage } from "../components/FlowPlay";
import { ClassifyStage } from "../components/rest/ClassifyStage";
import {
  asRecord,
  asRecordList,
  asUnknownList,
  classifyKind,
  ioOutputs,
  readBoolean,
  readNumber,
  readString,
  workflowInner,
  workflowStages,
} from "../components/rest/kernel";
import { RestHead } from "../components/rest/RestHead";
import { formatStatus } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const STAKE = "A quote is not a bill.";
const DEFAULT_SAMPLE = "MSG-E-MESSY";

interface InboxSample {
  readonly sample_id: string;
  readonly subject?: string;
  readonly kind?: string;
}

const INBOX_NODES: FlowNode[] = [
  { id: "email", label: "email", kind: "operator", room: "intake" },
  { id: "ap", label: "ap", kind: "operator", room: "pay" },
];

const INBOX_STEPS: FlowStep[] = [
  {
    id: "classify",
    title: "Classify the document",
    nodeId: "email",
    manipulations: ["Read the message", "Stamp a document class"],
  },
];

function samplesFromCatalog(catalog: unknown): InboxSample[] {
  const rec = asRecord(catalog);
  return asUnknownList(rec?.samples).flatMap((item, idx) => {
    const row = asRecord(item);
    const sampleId = readString(row, "sample_id");
    if (!sampleId) {
      return [];
    }
    return [
      {
        sample_id: sampleId,
        subject: readString(row, "subject") || `Sample ${idx + 1}`,
        kind: readString(row, "kind"),
      },
    ];
  });
}

function pickSource(catalog: unknown, selected: string): unknown {
  const rec = asRecord(catalog);
  const artifacts = asRecord(rec?.sample_artifacts);
  if (artifacts && selected in artifacts) {
    return artifacts[selected];
  }
  const emails = asUnknownList(rec?.emails);
  return emails.find((item) => readString(asRecord(item), "message_id") === selected) ?? null;
}

function asArtifact(source: unknown): unknown {
  const rec = asRecord(source);
  if (!rec) {
    return null;
  }
  if (rec.kind) {
    return rec;
  }
  return {
    kind: "email",
    artifact_id: rec.message_id,
    title: rec.subject,
    source_path: "ingestion/emails.json",
    record: rec,
    email: rec,
  };
}

function attachmentsOf(source: unknown): unknown[] {
  const rec = asRecord(source);
  if (!rec) {
    return [];
  }
  const direct = asUnknownList(rec.attachments);
  if (direct.length) {
    return direct;
  }
  return asUnknownList(asRecord(rec.email)?.attachments);
}

function inboxEdges(isInvoice: boolean): FlowEdge[] {
  return [
    {
      id: "email-ap",
      from: "email",
      to: "ap",
      label: isInvoice ? "vendor bill" : "not a bill",
      attached: isInvoice,
    },
  ];
}

function inboxLive(ran: boolean, isInvoice: boolean, result: unknown): LiveStage[] {
  if (!ran) {
    return [];
  }
  const mapped: LiveStage[] = workflowStages(result).map((stage) => {
    const rec = asRecord(stage);
    return {
      id: readString(rec, "id"),
      bot: readString(rec, "bot"),
      slug: readString(rec, "slug") || readString(rec, "bot"),
      label: readString(rec, "label"),
      status: readString(rec, "status"),
      detail: readString(rec, "detail"),
    };
  });
  if (mapped.some((stage) => stage.slug === "email" || stage.bot === "email" || stage.slug === "ap")) {
    return mapped;
  }
  if (isInvoice) {
    return [
      { slug: "email", status: "completed" },
      { slug: "ap", status: "completed" },
    ];
  }
  return [{ slug: "email", status: "completed" }];
}

export default function Inbox(): JSX.Element {
  const [catalog, setCatalog] = useState<unknown>(null);
  const [selected, setSelected] = useState<string>(DEFAULT_SAMPLE);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/inbox")
      .then(setCatalog)
      .catch(() => setCatalog(null));
  }, [result]);

  const samples = samplesFromCatalog(catalog);
  const source = pickSource(catalog, selected);
  const inner = workflowInner(result);
  const outputs = ioOutputs(inner);
  const classification = readString(outputs, "classification") || readString(inner, "classification");
  const docClass = classifyKind(classification);
  const isInvoice = readBoolean(outputs, "is_invoice") === true || docClass === "invoice";
  const extractedRec = asRecord(outputs?.extracted) ?? asRecord(inner?.extracted);
  const amount = readNumber(extractedRec, "amount");
  const ran = Boolean(inner && classification);
  const stages = workflowStages(result);

  return (
    <div className="rest-page">
      <RestHead title="What arrived" stake={STAKE} />
      <div className="rest-chip-row" aria-label="Documents to try">
        {samples.map((item) => (
          <button
            type="button"
            key={item.sample_id}
            className={`rest-chip${item.sample_id === selected ? " is-on" : ""}`}
            aria-pressed={item.sample_id === selected}
            onClick={() => setSelected(item.sample_id)}
          >
            <span>{item.subject}</span>
            {item.kind ? <span className="mono">{item.kind}</span> : null}
          </button>
        ))}
      </div>
      <ClassifyStage
        artifact={asArtifact(source)}
        attachments={attachmentsOf(source)}
        docClass={ran ? docClass : null}
        classLabel={classification ? formatStatus(classification) : "Not classified"}
        isInvoice={isInvoice}
        ran={ran}
        extracted={{
          vendor: readString(extractedRec, "vendor"),
          invoiceNumber: readString(extractedRec, "invoice_number") || readString(extractedRec, "vendor_invoice_number"),
          amount: amount != null ? usd(amount) : undefined,
          poNumber: readString(extractedRec, "po_number"),
        }}
      />
      <RunBar
        label="Identify this document"
        running={running}
        onRun={() => run("/api/workflows/invoice-ingestion", { sample_id: selected })}
        extra={
          <button type="button" className="btn" disabled={running} onClick={() => run("/api/workflows/inbox", {})}>
            Sort the inbox
          </button>
        }
      />
      <ErrorBox error={error} />
      <FlowPlay
        mode="live"
        nodes={INBOX_NODES}
        edges={inboxEdges(ran && isInvoice)}
        steps={INBOX_STEPS}
        liveStages={inboxLive(ran, isInvoice, result)}
      />
      {inner ? <ProcessPanel stages={asRecordList(stages)} handoffs={asUnknownList(inner.handoffs)} summary={readString(inner, "summary")} /> : null}
      <details className="rest-evidence">
        <summary>Evidence</summary>
        {asUnknownList(outputs?.canonical_invoices).map((item, idx) => {
          const rec = asRecord(item);
          return <SourceArtifactViewer key={readString(rec, "artifact_id") || `out-${idx}`} artifact={item} compact />;
        })}
        <p className="muted">{readString(inner, "classification_reason") || "Kernel classifies before anyone books a bill."}</p>
      </details>
    </div>
  );
}
