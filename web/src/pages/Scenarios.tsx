import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../api";
import { useWorkflow } from "../hooks";
import { ErrorBox, Pill } from "../layout/Shell";
import { ArtifactStack, BeforeAfterDiff, flattenInputs, ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { TraceIds } from "../components/Explain";
import { formatEvalCase, formatStatus, friendlyExpected } from "../copy";

export default function Scenarios() {
  const [cards, setCards] = useState<any[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get<{ scenarios: any[] }>("/api/scenarios").then((payload) => setCards(payload.scenarios || []));
  }, []);

  const inner = result?.result;
  const io = inner?.io;
  const selected = cards.find((item) => item.id === active) || cards.find((item) => item.id === result?.scenario?.id);

  return (
    <div>
      <div className="page-head">
        <div className="eyebrow">Live pitch</div>
        <h1>Demo scenarios</h1>
        <p className="lede">Each scenario is a live finance problem with original source documents. Run it to see what Maximor decided, then inspect the records. Expected fixture answers stay hidden until execution.</p>
      </div>
      <ErrorBox error={error} />
      <div className="grid-3">
        {cards.map((card) => (
          <div className="card" key={card.id}>
            <div className="split">
              <h2 style={{ margin: 0, textTransform: "none", letterSpacing: 0, color: "var(--text)", fontSize: 16 }}>{card.title}</h2>
              <Link to={card.href} className="muted">
                open
              </Link>
            </div>
            <p className="muted">{card.challenge || card.setup}</p>
            <div className="btn-row" style={{ marginTop: 12 }}>
              <button
                className="btn"
                onClick={() => setActive(card.id)}
              >
                Preview input
              </button>
              <button
                className="btn primary"
                disabled={running}
                onClick={() => {
                  setActive(card.id);
                  run(`/api/workflows/scenario/${card.id}`);
                }}
              >
                {running && active === card.id ? "Running…" : "Run demo"}
              </button>
            </div>
          </div>
        ))}
      </div>
      {selected ? (
        <div className="io-flow" style={{ marginTop: 18 }}>
          <div className="io-col">
            <div className="io-label">Original input</div>
            <ArtifactStack artifacts={io?.inputs ? flattenInputs(io.inputs) : selected.input_preview} />
          </div>
          <div className="io-arrow">→</div>
          <div className="io-col">
            <div className="io-label">System process</div>
            {inner ? <ProcessPanel stages={inner.stages} handoffs={inner.handoffs} summary={inner.summary} /> : <div className="card"><p className="muted">Run to see grain-bot steps.</p></div>}
          </div>
          <div className="io-arrow">→</div>
          <div className="io-col">
            <div className="io-label">Final output</div>
            {inner ? (
              <div className="stack">
                <div className="card">
                  <div className="split">
                    <strong>{result.scenario?.title || result.workflow}</strong>
                    <Pill>{result.status}</Pill>
                  </div>
                  <p>{inner.summary}</p>
                  <TraceIds ids={inner.record_ids || result.record_ids} />
                </div>
                {io?.before || io?.after ? (
                  <div className="card">
                    <h2>Before / after</h2>
                    <BeforeAfterDiff before={flattenState(io.before)} after={flattenState(io.after)} />
                  </div>
                ) : null}
                {Array.isArray(result.expected) && result.expected.length ? (
                  <div className="card">
                    <h2>Expected result (after run)</h2>
                    {result.expected.map((item: any) => (
                      <div key={item.case_id} className="muted">
                        <div>{formatEvalCase(item.case_id).title}</div>
                        <div>{friendlyExpected(item.expected)}</div>
                        <TraceIds ids={[item.case_id]} />
                      </div>
                    ))}
                  </div>
                ) : null}
                {flattenInputs(io?.outputs).slice(0, 6).map((item: any, idx: number) => (
                  <div className="card" key={item.artifact_id || idx}>
                    <SourceArtifactViewer artifact={item} compact />
                  </div>
                ))}
              </div>
            ) : (
              <div className="card">
                <p className="muted">Challenge: {selected.challenge}. Run the demo to see the produced records.</p>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function flattenState(value: any): Record<string, unknown> | null {
  if (!value || typeof value !== "object") return null;
  if (Array.isArray(value)) return null;
  const flat: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    if (item !== null && typeof item !== "object") flat[key] = item;
    else if (Array.isArray(item) && item.every((entry) => typeof entry !== "object")) flat[key] = item;
    else if (typeof item === "number" || typeof item === "string" || typeof item === "boolean") flat[key] = item;
  }
  return Object.keys(flat).length ? flat : null;
}
