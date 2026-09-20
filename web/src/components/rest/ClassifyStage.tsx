import { SourceArtifactViewer } from "../Demo";
import { formatStatus } from "../../copy";
import type { DocClass } from "./kernel";

export interface ClassifyExtracted {
  readonly vendor?: string;
  readonly invoiceNumber?: string;
  readonly amount?: string;
  readonly poNumber?: string;
}

export interface ClassifyStageProps {
  readonly artifact: unknown;
  readonly attachments: readonly unknown[];
  readonly docClass: DocClass | null;
  readonly classLabel: string;
  readonly isInvoice: boolean;
  readonly ran: boolean;
  readonly extracted: ClassifyExtracted;
}

function stampWord(docClass: DocClass | null): string {
  if (!docClass) {
    return "—";
  }
  if (docClass === "invoice") {
    return "INVOICE";
  }
  if (docClass === "quote") {
    return "QUOTE";
  }
  if (docClass === "statement") {
    return "STATEMENT";
  }
  if (docClass === "receipt") {
    return "RECEIPT";
  }
  return "OTHER";
}

export function ClassifyStage(props: ClassifyStageProps): JSX.Element {
  const { artifact, attachments, docClass, classLabel, isInvoice, ran, extracted } = props;
  const stampClass = docClass ? `rest-stamp is-${docClass}` : "rest-stamp is-idle";
  return (
    <div className="rest-inbox" aria-label="Classify stage">
      <div className="rest-inbox-doc">
        <SourceArtifactViewer artifact={artifact} />
        {attachments.map((att, idx) => {
          const rec = att && typeof att === "object" ? (att as Record<string, unknown>) : {};
          const key = String(rec.artifact_id || rec.attachment_id || rec.filename || idx);
          return (
            <div className="rest-inbox-att" key={key}>
              <SourceArtifactViewer
                artifact={rec.kind ? att : { kind: "document", ...rec, record: att }}
                compact
              />
            </div>
          );
        })}
      </div>
      <aside className="rest-inbox-stamp-col">
        <div className={stampClass} aria-label="Document class">
          <span className="rest-stamp-mark">{stampWord(docClass)}</span>
          <span className="rest-stamp-label">{ran ? classLabel : "Not classified"}</span>
        </div>
        {ran ? (
          <p className="muted rest-stamp-note">
            {isInvoice ? "Handed to payables as a vendor bill." : "No vendor bill created."}
          </p>
        ) : (
          <p className="muted rest-stamp-note">Run classify to stamp the Kernel class.</p>
        )}
        {ran ? (
          <dl className="kv rest-stamp-kv">
            <dt>Vendor</dt>
            <dd>{extracted.vendor || "—"}</dd>
            <dt>Invoice number</dt>
            <dd>{extracted.invoiceNumber || "—"}</dd>
            <dt>Amount</dt>
            <dd>{extracted.amount || "—"}</dd>
            <dt>Purchase order</dt>
            <dd className="mono">{extracted.poNumber || "—"}</dd>
          </dl>
        ) : null}
        {ran && docClass && docClass !== "invoice" ? (
          <p className="muted">{formatStatus(docClass)} is not money the company owes.</p>
        ) : null}
      </aside>
    </div>
  );
}
