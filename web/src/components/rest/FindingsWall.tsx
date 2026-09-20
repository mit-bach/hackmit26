import { useState } from "react";
import { statusTone } from "../../api";
import { formatControlResult, formatStatus } from "../../copy";
import { Pill } from "../../layout/Shell";
import { TraceIds } from "../Explain";
import { asRecord, readString, readStringList } from "./kernel";

export interface FindingTile {
  readonly finding_id?: string;
  readonly title?: string;
  readonly summary?: string;
  readonly detail?: string;
  readonly description?: string;
  readonly control_id?: string;
  readonly control_name?: string;
  readonly severity?: string;
  readonly result?: string;
  readonly status?: string;
  readonly severity_rationale?: string;
  readonly reason_code?: string;
  readonly record_ids?: unknown;
  readonly evidence_ids?: unknown;
  readonly source_ids?: unknown;
  readonly affected_object_ids?: unknown;
}

export interface FindingCopy {
  readonly found: string;
  readonly why: string;
  readonly result: string;
}

export function explainFinding(item: FindingTile): FindingCopy {
  const blob = [
    item.title,
    item.summary,
    item.detail,
    item.description,
    item.control_id,
    item.control_name,
    readStringList(item.record_ids).join(" "),
    readStringList(item.affected_object_ids).join(" "),
  ]
    .join(" ")
    .toLowerCase();
  if (blob.includes("self") || blob.includes("same user") || blob.includes("apr-inv-self")) {
    return {
      found: "This invoice was requested, prepared, reviewed, and approved by the same user.",
      why: "Separation of duties expects different people or roles to prepare and approve a transaction.",
      result: "The audit agent recorded a control failure on this approval path.",
    };
  }
  if (blob.includes("duplicate invoice") || blob.includes("inv-006") || (blob.includes("duplicate") && blob.includes("invoice"))) {
    return {
      found: "These two invoices appear to request payment for the same vendor bill.",
      why: "Paying both would mean paying the vendor twice for one shipment.",
      result: "The duplicate pair is flagged so payables can hold the extra bill.",
    };
  }
  if (blob.includes("duplicate vendor") || blob.includes("vend-001")) {
    return {
      found: "Two vendor records look like the same supplier stored twice.",
      why: "Duplicate vendor masters make it easier to pay the wrong party or hide a second payment channel.",
      result: "The auditor flagged the vendor pair for master-data review.",
    };
  }
  if (blob.includes("round")) {
    return {
      found: item.summary || "One or more payments were unusually round amounts.",
      why: "Round-number payments can be legitimate, but the audit policy marks them for extra testing when other support is weak.",
      result: "The payments remain on the exception list until supporting invoices are confirmed.",
    };
  }
  if (blob.includes("missing") || blob.includes("support")) {
    return {
      found: "A payment exists without the expected invoice or supporting record that justifies it.",
      why: "Cash should not leave the company without a bill, receiving record, or other support.",
      result: "The payment is flagged as missing support.",
    };
  }
  if (blob.includes("post-close") || blob.includes("post close")) {
    return {
      found: "A journal entry was posted after the month was supposed to be locked.",
      why: "Post-close entries can change financial statements after they were treated as finished.",
      result: "The auditor flagged the post-close journal.",
    };
  }
  return {
    found: item.summary || item.detail || item.description || item.title || "A control test did not pass.",
    why: item.severity_rationale || item.reason_code || "The sampled records did not meet the control's expected pattern.",
    result: formatControlResult(item.severity || item.result || item.status),
  };
}

export function findingFromUnknown(value: unknown): FindingTile | null {
  const rec = asRecord(value);
  if (!rec) {
    return null;
  }
  return {
    finding_id: readString(rec, "finding_id"),
    title: readString(rec, "title"),
    summary: readString(rec, "summary"),
    detail: readString(rec, "detail"),
    description: readString(rec, "description"),
    control_id: readString(rec, "control_id"),
    control_name: readString(rec, "control_name"),
    severity: readString(rec, "severity"),
    result: readString(rec, "result"),
    status: readString(rec, "status"),
    severity_rationale: readString(rec, "severity_rationale"),
    reason_code: readString(rec, "reason_code"),
    record_ids: rec.record_ids,
    evidence_ids: rec.evidence_ids,
    source_ids: rec.source_ids,
    affected_object_ids: rec.affected_object_ids,
  };
}

function severityFill(severity: string | undefined): "bad" | "warn" | "info" | "neutral" {
  const value = (severity || "").toLowerCase();
  if (["high", "fail", "critical", "error", "open"].some((token) => value.includes(token))) {
    return "bad";
  }
  if (["medium", "warn", "moderate"].some((token) => value.includes(token))) {
    return "warn";
  }
  if (["low", "info", "note"].some((token) => value.includes(token))) {
    return "info";
  }
  return "neutral";
}

function recordIds(item: FindingTile): string[] {
  const merged = [
    ...readStringList(item.record_ids),
    ...readStringList(item.evidence_ids),
    ...readStringList(item.source_ids),
    ...readStringList(item.affected_object_ids),
  ];
  return Array.from(new Set(merged));
}

interface FindingsWallProps {
  readonly findings: readonly FindingTile[];
}

export function FindingsWall(props: FindingsWallProps): JSX.Element {
  const [openId, setOpenId] = useState<string | null>(null);
  if (!props.findings.length) {
    return (
      <div className="rest-findings is-empty" aria-label="Findings wall">
        <p className="muted">No findings yet. Run independent tests against the sampled books.</p>
      </div>
    );
  }
  return (
    <div className="rest-findings" aria-label="Findings wall">
      {props.findings.map((item, idx) => {
        const id = item.finding_id || `finding-${idx}`;
        const selected = openId === id;
        const fill = severityFill(item.severity || item.result);
        const copy = selected ? explainFinding(item) : null;
        const title = item.control_name ? formatStatus(item.control_name) : item.title || "Control finding";
        return (
          <article
            key={id}
            className={`rest-finding rest-finding-${fill}${selected ? " is-open" : ""}`}
          >
            <button
              type="button"
              className="rest-finding-hit"
              aria-pressed={selected}
              onClick={() => setOpenId(selected ? null : id)}
            >
              <span className="rest-finding-top">
                <strong>{title}</strong>
                <Pill tone={statusTone(item.severity || item.result)}>{formatStatus(item.severity || item.result)}</Pill>
              </span>
              <span className="rest-finding-result">{formatControlResult(item.severity || item.result || item.status)}</span>
            </button>
            <TraceIds ids={recordIds(item)} />
            {copy ? (
              <div className="rest-finding-explain">
                <p>{copy.found}</p>
                <p className="muted">{copy.why}</p>
                <p>{copy.result}</p>
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}
