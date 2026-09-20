import { statusTone } from "../../api";
import { formatFamily } from "../../copy";
import { Pill } from "../../layout/Shell";
import { asRecord, readNumber, readString } from "./kernel";

export const FAMILY_ORDER = [
  "documents",
  "cash",
  "anti_hack",
  "questions",
  "rubrics",
  "consistency",
  "long_horizon",
  "memory",
  "recovery",
] as const;

export type FamilyId = (typeof FAMILY_ORDER)[number];

export interface FamilyScore {
  readonly passed?: number;
  readonly total?: number;
  readonly rate?: number;
}

export interface Scorecard {
  readonly scenarios_passed?: number;
  readonly total_scenarios?: number;
  readonly scenarios_failed?: number;
  readonly by_family?: Readonly<Record<string, FamilyScore>>;
  readonly cross_workflow_consistency_rate?: number;
  readonly cross_workflow_consistency?: number;
  readonly error_propagation_rate?: number;
  readonly unsupported_assertion_rate?: number;
  readonly unsupported_action_rate?: number;
  readonly recovery_rate?: number;
  readonly error_recovery?: number;
}

export function scorecardFromUnknown(value: unknown): Scorecard | null {
  const rec = asRecord(value);
  if (!rec) {
    return null;
  }
  const byFamilyRaw = asRecord(rec.by_family);
  const byFamily: Record<string, FamilyScore> = {};
  if (byFamilyRaw) {
    for (const [key, entry] of Object.entries(byFamilyRaw)) {
      const row = asRecord(entry);
      byFamily[key] = {
        passed: readNumber(row, "passed"),
        total: readNumber(row, "total"),
        rate: readNumber(row, "rate"),
      };
    }
  }
  return {
    scenarios_passed: readNumber(rec, "scenarios_passed"),
    total_scenarios: readNumber(rec, "total_scenarios"),
    scenarios_failed: readNumber(rec, "scenarios_failed"),
    by_family: byFamily,
    cross_workflow_consistency_rate: readNumber(rec, "cross_workflow_consistency_rate"),
    cross_workflow_consistency: readNumber(rec, "cross_workflow_consistency"),
    error_propagation_rate: readNumber(rec, "error_propagation_rate"),
    unsupported_assertion_rate: readNumber(rec, "unsupported_assertion_rate"),
    unsupported_action_rate: readNumber(rec, "unsupported_action_rate"),
    recovery_rate: readNumber(rec, "recovery_rate"),
    error_recovery: readNumber(rec, "error_recovery"),
  };
}

export function pct(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

interface GauntletBoardProps {
  readonly scorecard: Scorecard | null;
  readonly familyPlain: Readonly<Record<string, string>>;
}

function familyTitle(id: string, familyPlain: Readonly<Record<string, string>>): string {
  return familyPlain[id] || formatFamily(id);
}

export function GauntletBoard(props: GauntletBoardProps): JSX.Element {
  const { scorecard, familyPlain } = props;
  const scored = Boolean(scorecard && scorecard.total_scenarios != null);
  const passed = scorecard?.scenarios_passed;
  const total = scorecard?.total_scenarios;
  return (
    <div className="rest-gauntlet" aria-label="Kernel gauntlet scoreboard">
      <div className="rest-gauntlet-cells">
        {FAMILY_ORDER.map((id) => {
          const row = scorecard?.by_family?.[id];
          const filled = Boolean(row && row.total != null);
          return (
            <div key={id} className={filled ? "rest-g-cell is-filled" : "rest-g-cell is-hollow"}>
              <span className="rest-g-family">{familyTitle(id, familyPlain)}</span>
              {filled ? (
                <strong>
                  {row?.passed ?? 0}/{row?.total ?? 0}
                </strong>
              ) : (
                <span className="rest-g-hollow-mark" aria-hidden="true">
                  —
                </span>
              )}
            </div>
          );
        })}
      </div>
      {scored ? (
        <p className="rest-gauntlet-caption">
          {passed} / {total} — Kernel measure, not the office score.
        </p>
      ) : (
        <p className="rest-gauntlet-caption muted">Hidden gold. Cells fill after a scored Kernel run.</p>
      )}
    </div>
  );
}

export function familyPlainMap(gauntlet: unknown): Record<string, string> {
  const root = asRecord(gauntlet);
  const families = asRecord(root?.families);
  const out: Record<string, string> = {};
  if (!families) {
    return out;
  }
  for (const [key, value] of Object.entries(families)) {
    const row = asRecord(value);
    const plain = readString(row, "plain") || readString(row, "title");
    if (plain) {
      out[key] = plain;
    }
  }
  return out;
}

interface CaseMark {
  readonly caseId: string;
  readonly title: string;
  readonly family?: string;
  readonly passed: boolean | null;
}

export function caseMarkFromUnknown(value: unknown): CaseMark | null {
  const rec = asRecord(value);
  if (!rec) {
    return null;
  }
  const passedRaw = rec.passed;
  const passed = typeof passedRaw === "boolean" ? passedRaw : null;
  return {
    caseId: readString(rec, "case_id") || "",
    title: readString(rec, "title") || readString(rec, "prompt") || readString(rec, "case_id") || "Case",
    family: readString(rec, "family"),
    passed,
  };
}

interface CaseStripProps {
  readonly cases: readonly CaseMark[];
  readonly scored: boolean;
}

export function CaseStrip(props: CaseStripProps): JSX.Element | null {
  if (!props.cases.length) {
    return null;
  }
  return (
    <details className="rest-evidence">
      <summary>Cases</summary>
      <ul className="rest-case-strip">
        {props.cases.map((item) => (
          <li key={item.caseId || item.title}>
            <span>{item.title}</span>
            {item.passed == null || !props.scored ? (
              <Pill>Hidden</Pill>
            ) : (
              <Pill tone={statusTone(item.passed ? "pass" : "fail")}>{item.passed ? "Passed" : "Failed"}</Pill>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
}

export function readModesComparison(value: unknown): Record<string, unknown> | null {
  const rec = asRecord(value);
  return asRecord(rec?.comparison) ?? asRecord(asRecord(rec?.modes)?.comparison);
}
