import { useEffect, useState } from "react";
import { get, usd } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import {
  lookupFromUnknown,
  MemoryEvalBoard,
  MemoryPeriods,
  type MemoryLookupView,
} from "../components/rest/MemoryPeriods";
import { RestHead } from "../components/rest/RestHead";
import {
  asRecord,
  asRecordList,
  asUnknownList,
  ioOutputs,
  readNumber,
  readString,
  workflowInner,
  workflowStages,
} from "../components/rest/kernel";
import { formatAccountingMethod } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const STAKE = "Reuse a treatment only when current evidence still supports it.";

type MemoryThread = "harbor" | "stripe";
type MemoryView = "periods" | "eval";

function firstArtifactTitle(items: unknown[]): string | undefined {
  for (const item of items) {
    const title = readString(asRecord(item), "title");
    if (title) {
      return title;
    }
  }
  return undefined;
}

function harborBundle(data: unknown): Record<string, unknown> | null {
  return asRecord(asRecord(data)?.harbor);
}

function lookupFromResult(result: unknown): MemoryLookupView {
  const inner = workflowInner(result);
  const outputs = ioOutputs(inner);
  return lookupFromUnknown(outputs?.september_lookup);
}

export default function Memory(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [thread, setThread] = useState<MemoryThread>("harbor");
  const [view, setView] = useState<MemoryView>("periods");
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/memory")
      .then(setData)
      .catch(() => setData(null));
  }, [result]);

  const inner = workflowInner(result);
  const outputs = ioOutputs(inner);
  const workflowName = readString(asRecord(result), "workflow");
  const evalPayload = workflowName === "memory-eval" ? inner?.payload ?? inner : null;
  const lookup = lookupFromResult(result);
  const method = readString(outputs, "final_method") || lookup.method;
  const amount = readNumber(outputs, "final_amount") ?? lookup.amount;
  const ran = workflowName === "memory" && Boolean(inner);
  const harbor = harborBundle(data);
  const prior = asUnknownList(harbor?.prior_memory);
  const augustLabel = thread === "stripe" ? "August Stripe payout decision" : firstArtifactTitle(prior) || "Harbor Electric decision";
  const septemberLabel = thread === "stripe" ? "September payout re-check" : "September re-check";
  const stages = workflowStages(result);
  const journal = asRecord(outputs?.journal_entry);

  return (
    <div className="rest-page">
      <RestHead title="August still matters" stake={STAKE} />
      <div className="rest-chip-row" aria-label="Memory view">
        <button
          type="button"
          className={`rest-chip${view === "periods" && thread === "harbor" ? " is-on" : ""}`}
          aria-pressed={view === "periods" && thread === "harbor"}
          onClick={() => {
            setView("periods");
            setThread("harbor");
          }}
        >
          Harbor Electric
        </button>
        <button
          type="button"
          className={`rest-chip${view === "periods" && thread === "stripe" ? " is-on" : ""}`}
          aria-pressed={view === "periods" && thread === "stripe"}
          onClick={() => {
            setView("periods");
            setThread("stripe");
          }}
        >
          Stripe
        </button>
        <button
          type="button"
          className={`rest-chip${view === "eval" ? " is-on" : ""}`}
          aria-pressed={view === "eval"}
          onClick={() => setView("eval")}
        >
          Memory on vs off
        </button>
      </div>
      {view === "eval" ? (
        <MemoryEvalBoard payload={evalPayload} />
      ) : (
        <MemoryPeriods
          august={{ label: augustLabel, detail: "Saved evidence, method, amount, and reason." }}
          september={{
            label: septemberLabel,
            detail: ran && method ? formatAccountingMethod(method) + (amount != null ? ` at ${usd(amount)}` : "") : "Re-check current evidence before reuse.",
          }}
          lookup={ran ? { ...lookup, method, amount } : { reused: null, retrieved: [] }}
          ran={ran}
        />
      )}
      <RunBar
        label={thread === "stripe" ? "Replay Stripe memory" : "Replay Harbor Electric memory"}
        running={running}
        onRun={() => {
          setView("periods");
          run("/api/workflows/memory", { story: thread });
        }}
        extra={
          <button
            type="button"
            className="btn"
            disabled={running}
            onClick={() => {
              setView("eval");
              run("/api/workflows/memory-eval");
            }}
          >
            Compare memory on vs off
          </button>
        }
      />
      <ErrorBox error={error} />
      {inner && view === "periods" ? (
        <ProcessPanel stages={asRecordList(stages)} handoffs={asUnknownList(inner.handoffs)} summary={readString(inner, "summary")} />
      ) : null}
      <details className="rest-evidence">
        <summary>Evidence</summary>
        {prior.map((item, idx) => (
          <SourceArtifactViewer key={readString(asRecord(item), "artifact_id") || `prior-${idx}`} artifact={item} />
        ))}
        <SourceArtifactViewer artifact={harbor?.history_table} />
        {journal ? (
          <SourceArtifactViewer
            artifact={{
              kind: "journal_entry",
              artifact_id: readString(journal, "entry_id") || "harbor-je",
              title: "September journal",
              source_path: "memory.scenarios",
              record: journal,
            }}
          />
        ) : null}
      </details>
    </div>
  );
}
