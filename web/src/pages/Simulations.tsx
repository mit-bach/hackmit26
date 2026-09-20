import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, statusTone } from "../api";
import { ArtifactStack, BeforeAfterDiff, flattenInputs, ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FlowPlay, type FlowEdge, type FlowNode, type FlowNodeKind, type FlowStep } from "../components/FlowPlay";
import { RestHead } from "../components/rest/RestHead";
import { asLiveStages, asRecord, asRecordList, asUnknownList, ioInputs, ioOutputs, readString, workflowInner, workflowStages } from "../components/rest/kernel";
import { SimulationCard } from "../components/SimulationCard";
import { TraceIds } from "../components/Explain";
import { AGENTS_BY_SLUG } from "../data/agents";
import { SIMULATIONS, SIMULATIONS_BY_ID, type Simulation } from "../data/simulations";
import { formatEvalCase, formatFieldKey, formatStatus, friendlyExpected } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill } from "../layout/Shell";

const STAKE = "Status is Runnable until this machine scored the case.";

export default function Simulations(): JSX.Element {
  const { id } = useParams();
  const selected = id ? SIMULATIONS_BY_ID[id] : null;
  if (id && !selected) {
    return (
      <div className="rest-page">
        <RestHead title="Simulation not found" stake="That id is not in the catalog." />
        <Link to="/simulations">Back to simulations</Link>
      </div>
    );
  }
  return selected ? <SimulationDetail item={selected} /> : <SimulationIndex />;
}

function SimulationIndex(): JSX.Element {
  const [cards, setCards] = useState<unknown[]>([]);
  useEffect(() => {
    get("/api/scenarios")
      .then((payload) => {
        const rec = asRecord(payload);
        setCards(asUnknownList(rec?.scenarios));
      })
      .catch(() => setCards([]));
  }, []);
  const byId: Record<string, unknown> = {};
  for (const row of cards) {
    const id = readString(asRecord(row), "id");
    if (id) {
      byId[id] = row;
    }
  }

  return (
    <div className="rest-page rest-catalog">
      <RestHead title="Runnable cases" stake={STAKE} />
      <p className="muted rest-catalog-note">Live desks live in the office nav.</p>
      <div className="grid-2">
        {SIMULATIONS.map((item) => (
          <SimulationCard key={item.id} item={item} status={statusFor(byId[item.id])} />
        ))}
      </div>
    </div>
  );
}

function nodeKind(slug: string): FlowNodeKind {
  if (slug.startsWith("ctl-")) {
    return "verifier";
  }
  if (slug === "audit") {
    return "assurance";
  }
  return "operator";
}

function simulationFlow(item: Simulation): { nodes: FlowNode[]; edges: FlowEdge[]; steps: FlowStep[] } {
  const nodes: FlowNode[] = item.agents.map((slug, idx) => ({
    id: slug,
    label: slug,
    kind: nodeKind(slug),
    column: idx,
  }));
  const edges: FlowEdge[] = item.agents.slice(1).map((slug, idx) => ({
    id: `${item.agents[idx]}-${slug}`,
    from: item.agents[idx],
    to: slug,
    label: "handoff",
    attached: true,
  }));
  const steps: FlowStep[] = (item.process.length ? item.process : [item.title]).map((step, idx) => ({
    id: `step-${idx}`,
    title: step,
    nodeId: item.agents[Math.min(idx, Math.max(item.agents.length - 1, 0))] || "email",
    manipulations: [step],
  }));
  return { nodes, edges, steps };
}

function SimulationDetail({ item }: { item: Simulation }): JSX.Element {
  const [cards, setCards] = useState<unknown[]>([]);
  const { running, result, error, run } = useWorkflow();
  const [evals, setEvals] = useState<unknown>(null);
  const flow = simulationFlow(item);

  useEffect(() => {
    get("/api/scenarios")
      .then((payload) => setCards(asUnknownList(asRecord(payload)?.scenarios)))
      .catch(() => setCards([]));
    get("/api/evaluations")
      .then(setEvals)
      .catch(() => setEvals(null));
  }, [result]);

  const apiRow = cards.find((row) => readString(asRecord(row), "id") === item.id);
  const inner = workflowInner(result);
  const outputs = ioOutputs(inner);
  const inputs = ioInputs(inner);
  const scored = scoredCases(item, evals);
  const ran = Boolean(inner);
  const stages = workflowStages(result);
  const expectedRows = asUnknownList(asRecord(result)?.expected);

  return (
    <div className="rest-page rest-sim-detail">
      <RestHead title={item.title} stake="Expected answers stay hidden until this machine scores the case." />
      <p className="muted">{item.scenario}</p>
      <div className="btn-row rest-sim-run">
        <Link className="btn" to="/simulations">
          All simulations
        </Link>
        <Link className="btn" to={item.href}>
          Open live runner
        </Link>
        {apiRow ? (
          <button type="button" className="btn primary" disabled={running} onClick={() => run(`/api/workflows/scenario/${item.id}`)}>
            {running ? "Running…" : "Run this simulation"}
          </button>
        ) : item.runner === "cfo-cycle" ? (
          <button type="button" className="btn primary" disabled={running} onClick={() => run("/api/workflows/cfo-cycle")}>
            {running ? "Running…" : "Run the connected cycle"}
          </button>
        ) : null}
      </div>
      <ErrorBox error={error} />
      {flow.nodes.length ? (
        <FlowPlay mode="live" nodes={flow.nodes} edges={flow.edges} steps={flow.steps} liveStages={asLiveStages(result)} />
      ) : null}
      {ran ? <ProcessPanel stages={asRecordList(stages)} handoffs={asUnknownList(inner?.handoffs)} summary={readString(inner, "summary")} /> : null}
      {ran ? (
        <p>
          <Pill tone={statusTone(readString(asRecord(result), "status"))}>{formatStatus(readString(asRecord(result), "status"))}</Pill>
        </p>
      ) : null}
      <details className="rest-evidence">
        <summary>Evidence</summary>
        <h2>What makes it difficult</h2>
        <p>{item.difficulty}</p>
        <h2>Agents</h2>
        <p className="muted">{item.agents.map((slug) => AGENTS_BY_SLUG[slug]?.name).join(" · ")}</p>
        <h2>Process</h2>
        <ol className="plain-list">
          {item.process.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        {ran && expectedRows.length ? (
          <>
            <h2>Hidden expected outcome (after run)</h2>
            {expectedRows.map((row) => {
              const rec = asRecord(row);
              const caseId = readString(rec, "case_id") || "";
              return (
                <div key={caseId} className="muted">
                  <div>{formatEvalCase(caseId).title}</div>
                  <div>{friendlyExpected(rec?.expected)}</div>
                </div>
              );
            })}
          </>
        ) : null}
        {(item.evalCases || []).length ? (
          <>
            <h2>Evaluation cases</h2>
            {(item.evalCases || []).map((caseId) => {
              const copy = formatEvalCase(caseId);
              const row = scored[caseId];
              return (
                <div key={caseId} className="split">
                  <strong>{copy.title}</strong>
                  <Pill tone={row ? statusTone(row.passed ? "pass" : "fail") : "neutral"}>
                    {row ? (row.passed ? "Passed" : "Failed") : "Not scored here"}
                  </Pill>
                </div>
              );
            })}
          </>
        ) : null}
        {ran ? <TraceIds ids={asUnknownList(inner?.record_ids).map(String)} /> : null}
        {inputs ? <ArtifactStack artifacts={flattenInputs(inputs)} /> : null}
        {asUnknownList(asRecord(apiRow)?.input_preview).length && !inputs ? (
          <ArtifactStack artifacts={asUnknownList(asRecord(apiRow)?.input_preview)} />
        ) : null}
        {ran ? (
          <BeforeAfterDiff before={flattenState(asRecord(asRecord(inner?.io)?.before))} after={flattenState(asRecord(asRecord(inner?.io)?.after))} labelFor={formatFieldKey} />
        ) : null}
        {flattenInputs(outputs).slice(0, 4).map((artifact: unknown, idx: number) => {
          const rec = asRecord(artifact);
          return <SourceArtifactViewer key={readString(rec, "artifact_id") || `out-${idx}`} artifact={artifact} compact />;
        })}
      </details>
    </div>
  );
}

function statusFor(apiRow: unknown): { label: string; tone: string } {
  const status = readString(asRecord(apiRow), "status");
  if (status) {
    return { label: formatStatus(status), tone: statusTone(status) };
  }
  return { label: "Runnable", tone: "neutral" };
}

function scoredCases(item: Simulation, evals: unknown): Record<string, { passed: boolean }> {
  const out: Record<string, { passed: boolean }> = {};
  const rec = asRecord(evals);
  const latest = asRecord(rec?.latest);
  const cases = asUnknownList(latest?.cases).length ? asUnknownList(latest?.cases) : asUnknownList(rec?.catalog);
  for (const caseId of item.evalCases || []) {
    const row = cases.map(asRecord).find((entry) => readString(entry, "case_id") === caseId);
    const passed = row?.passed;
    if (typeof passed === "boolean") {
      out[caseId] = { passed };
    }
  }
  return out;
}

function flattenState(value: Record<string, unknown> | null): Record<string, unknown> | null {
  if (!value) {
    return null;
  }
  const flat: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    if (item !== null && typeof item !== "object") {
      flat[key] = item;
    } else if (Array.isArray(item) && item.every((entry) => typeof entry !== "object")) {
      flat[key] = item;
    }
  }
  return Object.keys(flat).length ? flat : null;
}
