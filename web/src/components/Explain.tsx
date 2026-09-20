import { ReactNode } from "react";
import { GLOSSARY } from "../copy";
import { FriendlyRaw } from "./Demo";

export function WhatsHappening({
  happening,
  figureOut,
  why,
}: {
  happening: ReactNode;
  figureOut?: ReactNode;
  why?: ReactNode;
}) {
  return (
    <div className="card story-card happening-card">
      <h2>What's happening?</h2>
      <p>{happening}</p>
      {figureOut ? (
        <>
          <h2>What Maximor needs to figure out</h2>
          <p>{figureOut}</p>
        </>
      ) : null}
      {why ? (
        <>
          <h2>Why it matters</h2>
          <p>{why}</p>
        </>
      ) : null}
    </div>
  );
}

export function StoryCard({
  title = "About this scenario",
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className="card story-card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

export function ResultBlock({
  found,
  why,
  evidence,
  result,
}: {
  found?: ReactNode;
  why?: ReactNode;
  evidence?: ReactNode;
  result?: ReactNode;
}) {
  return (
    <div className="result-block">
      {found ? (
        <section>
          <h2>What Maximor found</h2>
          <p>{found}</p>
        </section>
      ) : null}
      {why ? (
        <section>
          <h2>Why</h2>
          <p>{why}</p>
        </section>
      ) : null}
      {evidence ? (
        <section>
          <h2>Evidence</h2>
          {evidence}
        </section>
      ) : null}
      {result ? (
        <section>
          <h2>Result</h2>
          <p>{result}</p>
        </section>
      ) : null}
    </div>
  );
}

export function GlossaryTerm({ term, children }: { term: string; children?: ReactNode }) {
  const definition = GLOSSARY[term];
  if (!definition) return <>{children || term}</>;
  return (
    <abbr className="term" title={definition}>
      {children || term}
    </abbr>
  );
}

export function TraceIds({ ids, label = "Supporting records" }: { ids?: Array<string | null | undefined>; label?: string }) {
  const clean = (ids || []).map((item) => String(item || "").trim()).filter(Boolean);
  if (!clean.length) return null;
  return (
    <div className="trace-ids">
      <span className="trace-label">{label}</span>
      <span className="mono muted">{clean.join(" · ")}</span>
    </div>
  );
}

export function LineageChain({ steps }: { steps?: Array<{ title?: string; detail?: string; record_id?: string; role?: string }> }) {
  if (!steps?.length) return null;
  return (
    <ol className="lineage-chain">
      {steps.map((step, index) => (
        <li key={`${step.record_id || step.title}-${index}`}>
          <div className="lineage-title">{step.title || step.role}</div>
          <div>{step.detail}</div>
          {step.record_id ? <TraceIds ids={[step.record_id]} label="Record" /> : null}
        </li>
      ))}
    </ol>
  );
}

export function DevDetails({ raw, children }: { raw: unknown; children: ReactNode }) {
  return (
    <FriendlyRaw
      raw={raw}
      defaultTab="friendly"
      friendlyLabel="Explanation"
      rawLabel="Developer details"
      friendly={children}
    />
  );
}

export function Definition({ term }: { term: string }) {
  const definition = GLOSSARY[term];
  if (!definition) return null;
  return (
    <p className="muted definition">
      <strong>{term}.</strong> {definition}
    </p>
  );
}
