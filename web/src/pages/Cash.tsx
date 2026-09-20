import { useEffect, useMemo, useState } from "react";
import { get, statusTone } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep, type LiveStage } from "../components/FlowPlay";
import {
  HELIOS_FEE,
  NORTHSTAR_TXN,
  PairingLanes,
  pairsFromCashPayload,
  type PairRow,
} from "../components/boards/PairingLanes";
import { explainCashMatch, formatMatchType, formatStatus } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill, RunBar } from "../layout/Shell";

const STAKE = "Every deposit and withdrawal needs an explanation; this one does not have it.";

const CASH_STEPS: readonly FlowStep[] = [
  { id: "s-bank", title: "Bank statement", nodeId: "bank", manipulations: ["read deposits and withdrawals"] },
  { id: "s-cash", title: "Pair bank to books", nodeId: "cash", manipulations: ["match", "investigate"] },
  { id: "s-ctl", title: "Recheck pairs", nodeId: "ctl-cash", manipulations: ["verify"] },
  { id: "s-close", title: "Month close", nodeId: "close", manipulations: ["sign-off"], status: "blocked" },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function innerResult(result: unknown): Record<string, unknown> | undefined {
  if (!isRecord(result)) {
    return undefined;
  }
  if (isRecord(result.result)) {
    return result.result;
  }
  return result;
}

function readMatches(result: unknown, data: unknown): readonly unknown[] {
  const inner = innerResult(result);
  const report = isRecord(inner?.report)
    ? inner.report
    : isRecord(data) && isRecord(data.report)
      ? data.report
      : undefined;
  if (report && Array.isArray(report.matches)) {
    return report.matches;
  }
  const outputs = isRecord(inner?.io) && isRecord(inner.io.outputs) ? inner.io.outputs : undefined;
  if (outputs && Array.isArray(outputs.matches)) {
    return outputs.matches;
  }
  return [];
}

function featuredPack(result: unknown, data: unknown): unknown {
  if (isRecord(data) && data.featured_cases) {
    return data.featured_cases;
  }
  const inner = innerResult(result);
  if (isRecord(inner?.io) && inner.io.inputs) {
    return inner.io.inputs;
  }
  return undefined;
}

function artifactId(value: unknown): string {
  if (!isRecord(value)) {
    return "";
  }
  const record = isRecord(value.record) ? value.record : {};
  return String(value.artifact_id || record.transaction_id || record.entry_id || record.evidence_id || "");
}

function caseBundle(pack: unknown, key: string): Record<string, unknown> | undefined {
  if (!isRecord(pack)) {
    return undefined;
  }
  return isRecord(pack[key]) ? pack[key] : undefined;
}

function bankArtifactFor(pair: PairRow | undefined, data: unknown, result: unknown): unknown {
  if (!pair) {
    return undefined;
  }
  const pack = featuredPack(result, data);
  const bundles = ["unexplained", "fee_netted", "grouped"].map((key) => caseBundle(pack, key));
  for (const bundle of bundles) {
    if (artifactId(bundle?.bank) === pair.bank.id) {
      return bundle?.bank;
    }
  }
  if (isRecord(data) && Array.isArray(data.bank)) {
    const row = data.bank.find((item) => isRecord(item) && item.transaction_id === pair.bank.id);
    if (isRecord(row)) {
      return {
        artifact_id: pair.bank.id,
        kind: "bank_transaction",
        title: row.description || pair.bank.id,
        record: row,
      };
    }
  }
  return undefined;
}

function ledgerArtifactsFor(pair: PairRow | undefined, data: unknown, result: unknown): unknown[] {
  if (!pair) {
    return [];
  }
  const pack = featuredPack(result, data);
  const bundles = ["unexplained", "fee_netted", "grouped"].map((key) => caseBundle(pack, key));
  for (const bundle of bundles) {
    if (artifactId(bundle?.bank) === pair.bank.id && Array.isArray(bundle?.ledger)) {
      return bundle.ledger;
    }
  }
  if (isRecord(data) && Array.isArray(data.ledger)) {
    const found: unknown[] = [];
    for (const chip of pair.ledger) {
      const row = data.ledger.find((item) => isRecord(item) && item.entry_id === chip.id);
      if (isRecord(row)) {
        found.push({
          artifact_id: row.entry_id,
          kind: "ledger_entry",
          title: row.description || row.entry_id,
          record: row,
        });
      }
    }
    return found;
  }
  return [];
}

function feeArtifactsFor(pair: PairRow | undefined, data: unknown, result: unknown): unknown[] {
  if (!pair || pair.bank.id === NORTHSTAR_TXN || pair.kind === "unexplained") {
    return [];
  }
  const pack = featuredPack(result, data);
  const bundle = caseBundle(pack, "fee_netted");
  if (artifactId(bundle?.bank) === pair.bank.id && Array.isArray(bundle?.fees)) {
    return bundle.fees;
  }
  if (isRecord(data) && Array.isArray(data.fees)) {
    return data.fees.filter((item) => isRecord(item) && pair.feeIds.includes(String(item.evidence_id || "")));
  }
  return [];
}

function asLiveStages(value: unknown): readonly LiveStage[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord).map((row) => ({
    id: typeof row.id === "string" ? row.id : undefined,
    bot: typeof row.bot === "string" ? row.bot : undefined,
    slug: typeof row.slug === "string" ? row.slug : undefined,
    label: typeof row.label === "string" ? row.label : undefined,
    status: typeof row.status === "string" ? row.status : undefined,
    detail: typeof row.detail === "string" ? row.detail : undefined,
  }));
}

function liveStagesOf(result: unknown): readonly LiveStage[] {
  const inner = innerResult(result);
  if (inner && Array.isArray(inner.stages)) {
    return asLiveStages(inner.stages);
  }
  if (inner && isRecord(inner.result) && Array.isArray(inner.result.stages)) {
    return asLiveStages(inner.result.stages);
  }
  return [];
}

export default function Cash(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [selectedId, setSelectedId] = useState(NORTHSTAR_TXN);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/cash")
      .then(setData)
      .catch(() => undefined);
  }, [result]);

  const pairs = useMemo(
    () =>
      pairsFromCashPayload({
        matches: readMatches(result, data),
        featuredCases: featuredPack(result, data),
      }),
    [data, result]
  );

  useEffect(() => {
    if (!pairs.some((pair) => pair.id === selectedId)) {
      const northstar = pairs.find((pair) => pair.bank.id === NORTHSTAR_TXN);
      setSelectedId(northstar?.id ?? pairs[0]?.id ?? NORTHSTAR_TXN);
    }
  }, [pairs, selectedId]);

  const selected = pairs.find((pair) => pair.id === selectedId) ?? pairs[0];
  const unexplained = pairs.some((pair) => pair.kind === "unexplained");
  const inner = innerResult(result);
  const story = selected
    ? explainCashMatch({
        match_type: selected.matchType,
        bank_amount: selected.bankAmount,
        ledger_amount: selected.ledgerAmount,
        ledger_entry_ids: selected.ledger.map((chip) => chip.id),
      })
    : undefined;

  const nodes: readonly FlowNode[] = [
    { id: "bank", label: "Bank", kind: "source", room: "intake" },
    { id: "cash", label: "Cash", kind: "operator", room: "cash" },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash" },
    {
      id: "close",
      label: "Close",
      kind: "operator",
      room: "books-close",
      status: unexplained ? "blocked" : "idle",
    },
  ];
  const edges: readonly FlowEdge[] = [
    { id: "bank-cash", from: "bank", to: "cash", label: "statement" },
    { id: "cash-ctl", from: "cash", to: "ctl-cash", label: "proposal" },
    { id: "ctl-close", from: "ctl-cash", to: "close", label: unexplained ? "blocked" : "sign-off" },
  ];

  const bankArtifact = bankArtifactFor(selected, data, result);
  const ledgerArtifacts = ledgerArtifactsFor(selected, data, result);
  const feeArtifacts = feeArtifactsFor(selected, data, result);

  return (
    <div className="cash-desk">
      <h1>Bank vs books</h1>
      <p className="cash-stake">{STAKE}</p>
      <PairingLanes pairs={pairs} selectedId={selected?.id ?? NORTHSTAR_TXN} onSelect={setSelectedId} />
      <div className="cash-run">
        <RunBar label="Reconcile bank to ledger" running={running} onRun={() => run("/api/workflows/bank-reconciliation")} />
        <ErrorBox error={error} />
        {selected ? (
          <Pill
            tone={statusTone(
              selected.kind === "unexplained" ? "unexplained" : selected.kind === "matched" ? "matched" : "review"
            )}
          >
            {formatMatchType(selected.matchType)} · {formatStatus(selected.status || selected.matchType)}
          </Pill>
        ) : null}
      </div>
      <FlowPlay nodes={nodes} edges={edges} steps={CASH_STEPS} mode="live" liveStages={liveStagesOf(result)} />
      <details className="cash-evidence">
        <summary>Evidence</summary>
        {story ? <p className="muted">{story.body}</p> : null}
        {selected?.feeIds.includes(HELIOS_FEE) ? (
          <p className="muted">
            Fee <span className="mono">{HELIOS_FEE}</span> sits on the Helios pair. It is not evidence for{" "}
            <span className="mono">{NORTHSTAR_TXN}</span>.
          </p>
        ) : null}
        {bankArtifact ? (
          <div className="card">
            <h2>Bank statement row</h2>
            <SourceArtifactViewer artifact={bankArtifact} />
          </div>
        ) : null}
        {ledgerArtifacts.map((item, index) => (
          <div className="card" key={artifactId(item) || String(index)}>
            <h2>Ledger row</h2>
            <SourceArtifactViewer artifact={item} compact />
          </div>
        ))}
        {feeArtifacts.map((item, index) => (
          <div className="card" key={artifactId(item) || `fee-${index}`}>
            <h2>Fee evidence</h2>
            <SourceArtifactViewer artifact={item} compact />
          </div>
        ))}
        {Array.isArray(inner?.stages) ? (
          <ProcessPanel
            stages={inner.stages as Array<{ id?: string; label?: string; status?: string; bot?: string; detail?: string }>}
            handoffs={Array.isArray(inner.handoffs) ? inner.handoffs : undefined}
            summary={typeof inner.summary === "string" ? inner.summary : undefined}
          />
        ) : null}
      </details>
    </div>
  );
}
