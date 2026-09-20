import { useEffect, useState } from "react";
import { get } from "../api";
import { ProcessPanel } from "../components/Demo";
import {
  CaseStrip,
  caseMarkFromUnknown,
  familyPlainMap,
  GauntletBoard,
  pct,
  readModesComparison,
  scorecardFromUnknown,
} from "../components/rest/GauntletBoard";
import { RestHead } from "../components/rest/RestHead";
import { asRecord, asRecordList, asUnknownList, readNumber, readString, workflowInner, workflowStages } from "../components/rest/kernel";
import { friendlyExpected } from "../copy";
import { useWorkflow } from "../hooks";
import { ErrorBox, RunBar } from "../layout/Shell";

const STAKE = "Same workflows, hidden expected outcomes.";

const STORY_KEYS = ["trap", "harbor", "stripe", "correction"] as const;
type StoryKey = (typeof STORY_KEYS)[number];

function storyLabel(id: StoryKey): string {
  if (id === "trap") {
    return "Trap";
  }
  if (id === "harbor") {
    return "Harbor";
  }
  if (id === "stripe") {
    return "Stripe";
  }
  return "Correction";
}

function storyLine(id: StoryKey, payload: unknown): string {
  const rec = asRecord(payload);
  if (!rec) {
    return "";
  }
  if (id === "trap") {
    return readString(rec, "detected") || readString(rec, "naive") || "";
  }
  if (id === "harbor") {
    return readString(rec, "explanation") || readString(rec, "september_decision") || "";
  }
  if (id === "stripe") {
    return readString(rec, "explanation") || readString(rec, "received") || "";
  }
  const explanation = rec.explanation;
  if (typeof explanation === "string") {
    return explanation;
  }
  return readString(asRecord(explanation), "narrative") || readString(rec, "october") || "";
}

function gauntletScorecard(result: unknown, gauntlet: unknown): ReturnType<typeof scorecardFromUnknown> {
  const workflow = readString(asRecord(result), "workflow");
  const inner = workflowInner(result);
  if (workflow === "gauntlet") {
    const payload = asRecord(inner?.payload) ?? inner;
    const fromRun = scorecardFromUnknown(payload?.scorecard) ?? scorecardFromUnknown(asRecord(payload)?.scorecard);
    if (fromRun) {
      return fromRun;
    }
    const nested = scorecardFromUnknown(inner?.scorecard);
    if (nested) {
      return nested;
    }
  }
  const latest = asRecord(asRecord(gauntlet)?.latest);
  return scorecardFromUnknown(latest?.scorecard);
}

function gauntletCases(result: unknown, gauntlet: unknown, evaluations: unknown): unknown[] {
  const workflow = readString(asRecord(result), "workflow");
  const inner = workflowInner(result);
  if (workflow === "gauntlet") {
    const payload = asRecord(inner?.payload) ?? inner;
    const fromPayload = asUnknownList(payload?.cases);
    if (fromPayload.length) {
      return fromPayload;
    }
  }
  const fromView = asUnknownList(asRecord(gauntlet)?.cases);
  if (fromView.length) {
    return fromView;
  }
  return asUnknownList(asRecord(gauntlet)?.catalog).length
    ? asUnknownList(asRecord(gauntlet)?.catalog)
    : asUnknownList(asRecord(evaluations)?.catalog);
}

export default function Evaluations(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [gauntlet, setGauntlet] = useState<unknown>(null);
  const [storyId, setStoryId] = useState<StoryKey | null>(null);
  const [story, setStory] = useState<unknown>(null);
  const { running, result, error, run } = useWorkflow();

  useEffect(() => {
    get("/api/evaluations")
      .then(setData)
      .catch(() => setData(null));
    get("/api/gauntlet")
      .then(setGauntlet)
      .catch(() => setGauntlet(null));
  }, [result]);

  useEffect(() => {
    if (!storyId) {
      setStory(null);
      return;
    }
    get(`/api/stories/${storyId}`)
      .then(setStory)
      .catch(() => setStory(null));
  }, [storyId]);

  const inner = workflowInner(result);
  const scorecard = gauntletScorecard(result, gauntlet);
  const cases = gauntletCases(result, gauntlet, data).flatMap((item) => {
    const mark = caseMarkFromUnknown(item);
    return mark ? [mark] : [];
  });
  const scored = Boolean(scorecard && scorecard.total_scenarios != null);
  const stages = workflowStages(result);
  const modes = readModesComparison(inner) ?? readModesComparison(gauntlet);
  const mem = asRecord(asRecord(modes)?.memory_on_vs_off);
  const shared = asRecord(asRecord(modes)?.shared_state_on_vs_off);
  const evalResult = readString(asRecord(result), "workflow") === "evaluate" ? asRecord(inner?.payload) ?? inner : asRecord(data)?.latest;
  const evalRec = asRecord(evalResult);
  const evalPassed = readNumber(evalRec, "passed");
  const evalTotal = readNumber(evalRec, "total");

  return (
    <div className="rest-page">
      <RestHead title="Kernel gauntlet" stake={STAKE} />
      <GauntletBoard scorecard={scorecard} familyPlain={familyPlainMap(gauntlet)} />
      <RunBar
        label="Run Finance Gauntlet"
        running={running}
        onRun={() => run("/api/workflows/gauntlet")}
        extra={
          <>
            <button type="button" className="btn" disabled={running} onClick={() => run("/api/workflows/evaluate")}>
              Run the published finance cases
            </button>
            <button type="button" className="btn" disabled={running} onClick={() => run("/api/workflows/gauntlet", { modes: true })}>
              Compare memory on vs off
            </button>
          </>
        }
      />
      <ErrorBox error={error} />
      {inner ? <ProcessPanel stages={asRecordList(stages)} summary={readString(inner, "summary")} /> : null}
      <div className="rest-story-strip" aria-label="Related stories">
        {STORY_KEYS.map((id) => (
          <button
            type="button"
            key={id}
            className={`rest-chip${storyId === id ? " is-on" : ""}`}
            aria-pressed={storyId === id}
            onClick={() => setStoryId(storyId === id ? null : id)}
          >
            {storyLabel(id)}
          </button>
        ))}
      </div>
      {storyId && storyLine(storyId, story) ? <p className="muted rest-story-line">{storyLine(storyId, story)}</p> : null}
      {evalPassed != null && evalTotal != null ? (
        <p className="muted">
          Published cases {evalPassed} / {evalTotal}. Kernel measure, not the office score.
        </p>
      ) : null}
      {modes ? (
        <details className="rest-evidence">
          <summary>Memory and shared-state switches</summary>
          <p>
            Memory on {pct(readNumber(mem, "on"))} vs off {pct(readNumber(mem, "off"))}. Shared state on {pct(readNumber(shared, "on"))} vs
            off {pct(readNumber(shared, "off"))}. Kernel measure, not the office score.
          </p>
        </details>
      ) : null}
      <CaseStrip cases={cases} scored={scored} />
      {scored ? (
        <details className="rest-evidence">
          <summary>Kernel rates</summary>
          <dl className="kv">
            <dt>Cross-workflow consistency</dt>
            <dd>{pct(scorecard?.cross_workflow_consistency_rate ?? scorecard?.cross_workflow_consistency)}</dd>
            <dt>Error propagation</dt>
            <dd>{pct(scorecard?.error_propagation_rate)}</dd>
            <dt>Unsupported claims</dt>
            <dd>{pct(scorecard?.unsupported_assertion_rate ?? scorecard?.unsupported_action_rate)}</dd>
            <dt>Recovery</dt>
            <dd>{pct(scorecard?.recovery_rate ?? scorecard?.error_recovery)}</dd>
          </dl>
          <p className="muted">These percentages are a Kernel measure, not the office score.</p>
        </details>
      ) : null}
      {scored ? (
        <details className="rest-evidence">
          <summary>Actual vs hidden expected (after run)</summary>
          {gauntletCases(result, gauntlet, data).map((item, idx) => {
            const rec = asRecord(item);
            if (!rec || rec.expected == null) {
              return null;
            }
            return (
              <p key={readString(rec, "case_id") || `exp-${idx}`} className="muted">
                {readString(rec, "case_id")}: {friendlyExpected(rec.actual)}
              </p>
            );
          })}
        </details>
      ) : null}
    </div>
  );
}
