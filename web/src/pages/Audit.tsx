import { useEffect, useState } from "react";
import { get } from "../api";
import { ProcessPanel, SourceArtifactViewer } from "../components/Demo";
import { FindingsWall, findingFromUnknown, type FindingTile } from "../components/rest/FindingsWall";
import { asRecord, asRecordList, asUnknownList, ioOutputs, readString, workflowInner, workflowStages } from "../components/rest/kernel";
import { RestHead } from "../components/rest/RestHead";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const STAKE = "Audit samples after the fact; it does not pay bills.";

function findingsFromResult(result: unknown): FindingTile[] {
  const inner = workflowInner(result);
  const outputs = ioOutputs(inner);
  const fromOutputs = asUnknownList(outputs?.findings);
  const fromRun = asUnknownList(asRecord(inner?.run)?.findings);
  const fromPayload = asUnknownList(asRecord(asRecord(inner?.payload)?.run)?.findings);
  const raw = fromOutputs.length ? fromOutputs : fromRun.length ? fromRun : fromPayload;
  return raw.flatMap((item) => {
    const tile = findingFromUnknown(item);
    return tile ? [tile] : [];
  });
}

function featuredArtifacts(data: unknown): unknown[] {
  const rec = asRecord(data);
  const inputs = asRecord(rec?.inputs);
  const featured = asRecord(inputs?.featured);
  if (!featured) {
    return [];
  }
  return Object.values(featured).filter(Boolean);
}

export default function Audit(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/audit")
      .then(setData)
      .catch(() => setData(null));
  }, [result]);

  const inner = workflowInner(result);
  const findings = findingsFromResult(result);
  const stages = workflowStages(result);
  const featured = featuredArtifacts(data);

  return (
    <div className="rest-page">
      <RestHead title="Independent tests" stake={STAKE} />
      <FindingsWall findings={findings} />
      <RunBar label="Run independent audit" running={running} onRun={() => run("/api/workflows/audit")} />
      <ErrorBox error={error} />
      {inner ? <ProcessPanel stages={asRecordList(stages)} handoffs={asUnknownList(inner.handoffs)} summary={readString(inner, "summary")} /> : null}
      <details className="rest-evidence">
        <summary>Evidence</summary>
        {featured.map((item, idx) => {
          const rec = asRecord(item);
          return <SourceArtifactViewer key={readString(rec, "artifact_id") || `feat-${idx}`} artifact={item} compact />;
        })}
        <p className="muted">{readString(asRecord(data), "note") || "Planted answers are not shown before the run."}</p>
      </details>
    </div>
  );
}
