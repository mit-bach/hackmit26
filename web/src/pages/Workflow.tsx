import { useEffect, useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FlowPlay, type FlowStep } from "../components/FlowPlay";
import { SHOW_STORIES, showStoryById, type ShowStory, type ShowStoryId } from "../data/showPath";

const STAKE =
  "The same identity must mean the same thing in payables, the bank, close, forecast, and audit.";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function withMonoIds(text: string, ids: readonly string[]): ReactNode {
  if (ids.length === 0) {
    return text;
  }
  const pattern = new RegExp(`(${ids.map(escapeRegExp).join("|")})`);
  return text.split(pattern).map((part, index) =>
    ids.includes(part) ? (
      <span className="mono" key={`${part}-${index}`}>
        {part}
      </span>
    ) : (
      part
    )
  );
}

function CaseMeta(props: { story: ShowStory }): JSX.Element {
  const { story } = props;
  if (story.amount) {
    return (
      <span className="docket-case-meta">
        {story.vendor} · <span className="docket-amt">{story.amount}</span> · {story.outcome}
      </span>
    );
  }
  return (
    <span className="docket-case-meta">
      {story.vendor} · {story.outcome}
    </span>
  );
}

function CaseFileButton(props: {
  story: ShowStory;
  active: boolean;
  onSelect: (id: ShowStoryId) => void;
}): JSX.Element {
  const { story, active, onSelect } = props;
  return (
    <button
      type="button"
      className={active ? "docket-case active" : "docket-case"}
      aria-pressed={active}
      onClick={() => onSelect(story.id)}
    >
      <span className="docket-case-label">{story.label}</span>
      <CaseMeta story={story} />
      <span className="docket-case-ids">
        {story.previewIds.map((id) => (
          <span className="mono" key={id}>
            {id}
          </span>
        ))}
      </span>
    </button>
  );
}

function StepNow(props: { step: FlowStep | undefined }): JSX.Element | null {
  const { step } = props;
  if (!step) {
    return null;
  }
  const chips = step.manipulations.slice(0, 3);
  return (
    <div className="step-now">
      <h2>{step.title}</h2>
      {chips.length > 0 ? (
        <div className="step-now-chips">
          {chips.map((item) => (
            <span className="pill" key={item}>
              {item}
            </span>
          ))}
        </div>
      ) : null}
      {step.handoff ? (
        <p className="step-now-handoff">
          Handle to {step.handoff.to}: {step.handoff.why}
        </p>
      ) : null}
    </div>
  );
}

export default function Workflow(): JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams();
  const story = showStoryById(searchParams.get("story"));
  const [stepId, setStepId] = useState(story.steps[0]?.id ?? "");

  useEffect(() => {
    setStepId(story.steps[0]?.id ?? "");
  }, [story.id, story.steps]);

  function selectStory(id: ShowStoryId): void {
    setSearchParams({ story: id });
  }

  const currentStep = story.steps.find((step) => step.id === stepId) ?? story.steps[0];

  return (
    <div>
      <h1>Three invoices, one set of books</h1>
      <p className="docket-stake">{STAKE}</p>
      <div className="docket">
        <aside className="docket-rail" aria-label="Case files">
          {SHOW_STORIES.map((item) => (
            <CaseFileButton
              key={item.id}
              story={item}
              active={item.id === story.id}
              onSelect={selectStory}
            />
          ))}
        </aside>
        <section className="docket-stage">
          <div className="id-ticker" aria-label="Case identities">
            {story.ids.map((id) => (
              <span className="mono" key={id}>
                {id}
              </span>
            ))}
          </div>
          <FlowPlay
            key={story.id}
            mode="story"
            autoplay
            nodes={story.nodes}
            edges={story.edges}
            steps={story.steps}
            onStepChange={setStepId}
          />
          <StepNow step={currentStep} />
          <div className="docket-exits">
            {story.exits.map((exit) => (
              <Link key={`${exit.href}:${exit.label}`} className="docket-exit" to={exit.href}>
                {withMonoIds(exit.label, exit.ids)}
              </Link>
            ))}
          </div>
          <details className="docket-list">
            <summary>Read as a list</summary>
            <ol>
              {story.steps.map((step, index) => (
                <li key={step.id}>
                  <strong>
                    {index + 1}. {step.title}
                  </strong>
                  {step.body ? <p>{step.body}</p> : null}
                </li>
              ))}
            </ol>
          </details>
        </section>
      </div>
    </div>
  );
}
