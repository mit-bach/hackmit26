import { useEffect, useState } from "react";
import { get, statusTone } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowStep, type LiveStage } from "../components/FlowPlay";
import { StripeWaterfall } from "../components/boards/StripeWaterfall";
import { formatStatus } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill } from "../layout/Shell";

const STAKE = "Gross minus refunds, disputes, and fees should equal the bank deposit.";

const STRIPE_STEPS: readonly FlowStep[] = [
  { id: "s-stripe", title: "Unpack payout", nodeId: "stripe", manipulations: ["charges", "refunds", "fees"] },
  { id: "s-cash", title: "Tie to bank", nodeId: "cash", manipulations: ["match deposit"] },
  { id: "s-apply", title: "Apply to books", nodeId: "apply", manipulations: ["cash apply"] },
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

function readPayouts(result: unknown, data: unknown): readonly unknown[] {
  const inner = innerResult(result);
  if (inner && Array.isArray(inner.payouts)) {
    return inner.payouts;
  }
  if (isRecord(data) && Array.isArray(data.payouts)) {
    return data.payouts;
  }
  return [];
}

function payoutRecord(item: unknown): Record<string, unknown> | undefined {
  if (!isRecord(item)) {
    return undefined;
  }
  return isRecord(item.payout) ? item.payout : item;
}

function payoutIdOf(item: unknown): string {
  const payout = payoutRecord(item);
  return payout ? String(payout.payout_id || "") : "";
}

function breakdownOf(item: unknown): unknown {
  return isRecord(item) ? item.breakdown : undefined;
}

function finiteOrNull(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function depositOf(item: unknown, bundle: unknown): number | null {
  const payout = payoutRecord(item);
  if (payout && payout.bank_deposit_amount !== undefined && payout.bank_deposit_amount !== null) {
    return finiteOrNull(payout.bank_deposit_amount);
  }
  const bd = isRecord(breakdownOf(item)) ? breakdownOf(item) : undefined;
  if (isRecord(bd) && bd.bank_deposit_amount !== undefined && bd.bank_deposit_amount !== null) {
    return finiteOrNull(bd.bank_deposit_amount);
  }
  if (isRecord(bundle) && isRecord(bundle.bank_deposit) && isRecord(bundle.bank_deposit.record)) {
    return finiteOrNull(bundle.bank_deposit.record.amount);
  }
  return null;
}

function isTied(item: unknown): boolean {
  return isRecord(item) && item.tied === true;
}

function stripeMode(data: unknown): string {
  if (isRecord(data) && isRecord(data.mode) && data.mode.mode) {
    return String(data.mode.mode);
  }
  return "simulated";
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

function bundleFor(payoutId: string, data: unknown, result: unknown): unknown {
  if (payoutId && isRecord(data) && isRecord(data.bundles) && data.bundles[payoutId]) {
    return data.bundles[payoutId];
  }
  const inner = innerResult(result);
  if (inner && isRecord(inner.io)) {
    return inner.io.inputs;
  }
  return undefined;
}

export default function Stripe(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [index, setIndex] = useState(0);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/stripe")
      .then(setData)
      .catch(() => undefined);
  }, [result]);

  const payouts = readPayouts(result, data);
  const current = payouts[index] ?? payouts[0];
  const payoutId = payoutIdOf(current);
  const bundle = bundleFor(payoutId, data, result);
  const bd = breakdownOf(current);
  const deposit = depositOf(current, bundle);
  const tied = isTied(current);
  const mode = stripeMode(data);
  const live = mode === "live";
  const inner = innerResult(result);

  const nodes: readonly FlowNode[] = [
    { id: "stripe", label: "Stripe", kind: "source", room: "intake" },
    { id: "cash", label: "Cash", kind: "operator", room: "cash" },
    { id: "apply", label: "Apply", kind: "operator", room: "cash" },
    { id: "ctl-cash", label: "ctl-cash", kind: "verifier", room: "cash" },
  ];
  const edges: readonly FlowEdge[] = [
    { id: "stripe-cash", from: "stripe", to: "cash", label: "payout" },
    { id: "stripe-apply", from: "stripe", to: "apply", label: "apply" },
    {
      id: "cash-ctl",
      from: "cash",
      to: "ctl-cash",
      label: tied ? "tied" : "break",
      attached: current ? tied : true,
    },
  ];

  const exceptions = isRecord(bd) && Array.isArray(bd.exceptions) ? bd.exceptions : [];
  const balanceTxns =
    isRecord(bundle) && Array.isArray(bundle.balance_transactions) ? bundle.balance_transactions : [];

  return (
    <div className="cash-desk">
      <h1>Stripe payout</h1>
      <p className="cash-stake">{STAKE}</p>
      <div className="cash-stripe-toolbar">
        <Pill tone={live ? "warn" : "info"}>Stripe {formatStatus(mode)}</Pill>
        {current ? (
          <Pill tone={tied ? "ok" : "bad"}>{tied ? "Tied" : "Does not tie"}</Pill>
        ) : null}
      </div>
      {payouts.length > 0 ? (
        <div className="cash-payout-strip" aria-label="Payouts">
          {payouts.map((item, idx) => {
            const id = payoutIdOf(item) || `payout-${idx}`;
            return (
              <button
                key={id}
                type="button"
                className={idx === index ? "cash-payout-id is-selected" : "cash-payout-id"}
                aria-pressed={idx === index}
                onClick={() => setIndex(idx)}
              >
                <span className="mono">{id}</span>
              </button>
            );
          })}
        </div>
      ) : null}
      <div className="cash-stage cash-stage-waterfall">
        <StripeWaterfall breakdown={bd} deposit={deposit} tied={tied} />
      </div>
      <div className="cash-run">
        <div className="toolbar">
          <div className="btn-row">
            <button
              type="button"
              className="btn primary"
              disabled={running}
              onClick={() => run("/api/workflows/stripe-reconciliation")}
            >
              {running ? "Running…" : "Explain this payout"}
            </button>
          </div>
        </div>
        <ErrorBox error={error} />
      </div>
      <FlowPlay nodes={nodes} edges={edges} steps={STRIPE_STEPS} mode="live" liveStages={liveStagesOf(result)} />
      <details className="cash-evidence">
        <summary>Evidence</summary>
        {exceptions.map((item) => (
          <Pill key={String(item)} tone={statusTone(String(item))}>
            {formatStatus(item)}
          </Pill>
        ))}
        {isRecord(bundle) && bundle.payout ? (
          <div className="card">
            <h2>Payout</h2>
            <SourceArtifactViewer artifact={bundle.payout} />
          </div>
        ) : null}
        {balanceTxns.map((item, idx) => (
          <div className="card" key={isRecord(item) ? String(item.artifact_id || idx) : String(idx)}>
            <h2>Balance transaction</h2>
            <SourceArtifactViewer artifact={item} compact />
          </div>
        ))}
        {isRecord(bundle) && bundle.bank_deposit ? (
          <div className="card">
            <h2>Bank deposit</h2>
            <SourceArtifactViewer artifact={bundle.bank_deposit} />
          </div>
        ) : null}
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
