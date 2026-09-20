import { usd } from "../../api";
import { formatAccountingMethod } from "../../copy";
import { asRecord, readBoolean, readNumber, readString, readStringList } from "./kernel";

export interface PeriodChip {
  readonly label: string;
  readonly detail?: string;
}

export interface MemoryLookupView {
  readonly reused: boolean | null;
  readonly deviation?: string;
  readonly method?: string;
  readonly amount?: number;
  readonly retrieved: readonly string[];
}

interface MemoryPeriodsProps {
  readonly august: PeriodChip;
  readonly september: PeriodChip;
  readonly lookup: MemoryLookupView;
  readonly ran: boolean;
}

export function lookupFromUnknown(value: unknown): MemoryLookupView {
  const rec = asRecord(value);
  if (!rec) {
    return { reused: null, retrieved: [] };
  }
  const retrieved = readStringList(rec.retrieved).length
    ? readStringList(rec.retrieved)
    : readStringList(rec.retrieved_ids);
  const reused = readBoolean(rec, "precedent_used");
  const deviation = readString(rec, "deviation");
  const method = readString(rec, "final_method") || readString(rec, "method") || readString(rec, "selected_method");
  const amount = readNumber(rec, "amount") ?? readNumber(rec, "final_amount");
  return {
    reused: reused ?? null,
    deviation,
    method,
    amount,
    retrieved,
  };
}

export function MemoryPeriods(props: MemoryPeriodsProps): JSX.Element {
  const { august, september, lookup, ran } = props;
  const dashed = ran && lookup.reused === false;
  const solid = ran && lookup.reused === true;
  const arrowClass = dashed ? "rest-memory-arrow is-dashed" : solid ? "rest-memory-arrow is-solid" : "rest-memory-arrow is-idle";
  const methodLabel = lookup.method ? formatAccountingMethod(lookup.method) : null;
  return (
    <div className="rest-memory" aria-label="August and September">
      <section className="rest-period">
        <h2>August</h2>
        <div className="rest-period-chip">{august.label}</div>
        {august.detail ? <p className="muted">{august.detail}</p> : null}
      </section>
      <div className={arrowClass} aria-hidden="true">
        <svg viewBox="0 0 120 48" width="120" height="48">
          <line className="rest-memory-line" x1="8" y1="24" x2="96" y2="24" />
          <polygon className="rest-memory-head" points="96,14 112,24 96,34" />
        </svg>
        <span className="rest-memory-caption">
          {!ran ? "Retrieval" : solid ? "Reused" : dashed ? "Deviated" : "Retrieval"}
        </span>
      </div>
      <section className="rest-period">
        <h2>September</h2>
        <div className="rest-period-chip">{september.label}</div>
        {september.detail ? <p className="muted">{september.detail}</p> : null}
        {ran && methodLabel ? (
          <p>
            {methodLabel}
            {lookup.amount != null ? ` · ${usd(lookup.amount)}` : ""}
          </p>
        ) : null}
        {dashed && lookup.deviation ? <p className="rest-memory-dev">{lookup.deviation}</p> : null}
      </section>
    </div>
  );
}

interface MemoryEvalRow {
  readonly caseId: string;
  readonly onCorrect?: boolean;
  readonly offCorrect?: boolean;
}

interface MemoryEvalBoardProps {
  readonly payload: unknown;
}

function evalRows(payload: unknown): MemoryEvalRow[] {
  const rec = asRecord(payload);
  const cases = rec ? rec.cases : undefined;
  if (!Array.isArray(cases)) {
    return [];
  }
  return cases.map((item, idx) => {
    const row = asRecord(item);
    const on = asRecord(row?.memory_on);
    const off = asRecord(row?.memory_off);
    return {
      caseId: readString(row, "case_id") || `case-${idx}`,
      onCorrect: readBoolean(on, "correct"),
      offCorrect: readBoolean(off, "correct"),
    };
  });
}

export function MemoryEvalBoard(props: MemoryEvalBoardProps): JSX.Element {
  const rec = asRecord(props.payload);
  const metrics = asRecord(rec?.metrics);
  const on = asRecord(metrics?.memory_on) ?? asRecord(asRecord(metrics?.on));
  const off = asRecord(metrics?.memory_off) ?? asRecord(asRecord(metrics?.off));
  const rows = evalRows(props.payload);
  const onCorrect = readNumber(on, "correct");
  const onTotal = readNumber(on, "total");
  const offCorrect = readNumber(off, "correct");
  const offTotal = readNumber(off, "total");
  if (!rec) {
    return (
      <div className="rest-memory rest-memory-eval is-empty" aria-label="Memory on versus off">
        <p className="muted">Run the on vs off comparison to fill this view.</p>
      </div>
    );
  }
  return (
    <div className="rest-memory rest-memory-eval" aria-label="Memory on versus off">
      <section className="rest-period">
        <h2>Memory off</h2>
        <p className="rest-eval-score">
          {offCorrect != null && offTotal != null ? `${offCorrect} / ${offTotal}` : "—"}
        </p>
        <p className="muted">September estimates without last month's saved decision.</p>
      </section>
      <div className="rest-memory-arrow is-idle" aria-hidden="true">
        <span className="rest-memory-caption">Same input</span>
      </div>
      <section className="rest-period">
        <h2>Memory on</h2>
        <p className="rest-eval-score">
          {onCorrect != null && onTotal != null ? `${onCorrect} / ${onTotal}` : "—"}
        </p>
        <p className="muted">September may retrieve August, then re-check current evidence.</p>
      </section>
      {rows.length ? (
        <ul className="rest-eval-cases">
          {rows.map((row) => (
            <li key={row.caseId}>
              <span className="mono">{row.caseId}</span>
              <span>off {row.offCorrect == null ? "—" : row.offCorrect ? "match" : "miss"}</span>
              <span>on {row.onCorrect == null ? "—" : row.onCorrect ? "match" : "miss"}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
