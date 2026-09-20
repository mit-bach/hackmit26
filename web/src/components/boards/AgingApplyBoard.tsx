import { usd } from "../../api";
import { formatAgingBucket, formatDecision, formatStatus } from "../../copy";
import { Pill } from "../../layout/Shell";
import {
  AGING_BUCKETS,
  FEATURED_PAYMENT_ID,
  type AgingBucketKey,
  type CollectionChip,
  artifactRecord,
  asList,
  isRecord,
  num,
  str,
} from "./pay-util";

export { AGING_BUCKETS, FEATURED_PAYMENT_ID };
export type { CollectionChip };

export interface AgingSegment {
  readonly key: AgingBucketKey;
  readonly amount: number;
  readonly widthPct: number;
}

export interface ApplyPayment {
  readonly payment_id: string;
  readonly payer_name: string;
  readonly amount: number;
  readonly remittance_text: string;
  readonly payment_date?: string;
  readonly bank_reference?: string;
}

export interface ApplyInvoice {
  readonly invoice_id: string;
  readonly customer_name?: string;
  readonly outstanding_amount?: number;
  readonly description?: string;
}

export interface AgingApplyBoardProps {
  readonly data: unknown;
  readonly selectedBucket: string | null;
  readonly onSelectBucket: (key: AgingBucketKey) => void;
  readonly applyRan: boolean;
  readonly appliedIds: readonly string[];
  readonly applyDecision: string;
  readonly collectRan: boolean;
  readonly collectionActions: readonly CollectionChip[];
}

export function agingSegments(data: unknown): readonly AgingSegment[] {
  const rec = isRecord(data) ? data : {};
  const buckets = isRecord(rec.buckets) ? rec.buckets : {};
  const amounts = AGING_BUCKETS.map((key) => ({
    key,
    amount: num(buckets[key]) ?? 0,
  }));
  const outstanding = num(rec.outstanding);
  const total = outstanding && outstanding > 0 ? outstanding : amounts.reduce((sum, item) => sum + item.amount, 0);
  if (total <= 0) {
    return amounts.map((item) => ({ ...item, widthPct: 20 }));
  }
  return amounts.map((item) => ({
    ...item,
    widthPct: (item.amount / total) * 100,
  }));
}

export function invoiceIdsInBucket(data: unknown, bucket: string): readonly string[] {
  const rec = isRecord(data) ? data : {};
  const fromLines = idsFromRows(asList(rec.aging_lines), bucket);
  if (fromLines.length) {
    return fromLines;
  }
  return idsFromRows(asList(rec.invoices), bucket);
}

function idsFromRows(rows: readonly unknown[], bucket: string): string[] {
  const ids: string[] = [];
  for (const row of rows) {
    if (!isRecord(row)) {
      continue;
    }
    if (str(row.aging_bucket) !== bucket) {
      continue;
    }
    const id = str(row.invoice_id);
    if (id) {
      ids.push(id);
    }
  }
  return ids;
}

export function featuredPayment(data: unknown): ApplyPayment {
  const rec = isRecord(data) ? data : {};
  const featured = isRecord(rec.featured_payment) ? rec.featured_payment : {};
  const artifact = isRecord(featured.payment) ? featured.payment : {};
  const record = artifactRecord(artifact) || {};
  const listed = asList(rec.payments).find((item) => isRecord(item) && str(item.payment_id) === FEATURED_PAYMENT_ID);
  const row = isRecord(listed) ? listed : {};
  return {
    payment_id: str(record.payment_id) || str(row.payment_id) || FEATURED_PAYMENT_ID,
    payer_name: str(record.payer_name) || str(row.payer_name) || "Lumen Labs",
    amount: num(record.amount) ?? num(row.amount) ?? 5000,
    remittance_text: str(record.remittance_text) || str(row.remittance_text) || str(record.description) || "September billing",
    payment_date: str(record.payment_date) || str(row.payment_date) || str(record.date),
    bank_reference: str(record.bank_reference) || str(row.bank_reference) || str(record.reference),
  };
}

export function competingInvoices(data: unknown, payment: ApplyPayment): readonly ApplyInvoice[] {
  const rec = isRecord(data) ? data : {};
  const featured = isRecord(rec.featured_payment) ? rec.featured_payment : {};
  const fromFeatured = asList(featured.candidate_invoices)
    .map((item) => invoiceFromUnknown(item))
    .filter((item): item is ApplyInvoice => Boolean(item));
  if (fromFeatured.length) {
    return fromFeatured;
  }
  const payer = payment.payer_name.toLowerCase();
  const open: ApplyInvoice[] = [];
  for (const item of asList(rec.invoices)) {
    const invoice = invoiceFromUnknown(item);
    if (!invoice) {
      continue;
    }
    const outstanding = invoice.outstanding_amount ?? 0;
    if (outstanding <= 0) {
      continue;
    }
    const name = (invoice.customer_name || "").toLowerCase();
    const sameCustomer = payer && name.includes(payer);
    const sameAmount = invoice.outstanding_amount !== undefined && Math.abs(invoice.outstanding_amount - payment.amount) < 0.005;
    if (sameCustomer || sameAmount) {
      open.push(invoice);
    }
  }
  return open;
}

function invoiceFromUnknown(value: unknown): ApplyInvoice | undefined {
  const record = artifactRecord(value) || (isRecord(value) ? value : undefined);
  if (!record) {
    return undefined;
  }
  const id = str(record.invoice_id);
  if (!id) {
    return undefined;
  }
  return {
    invoice_id: id,
    customer_name: str(record.customer_name),
    outstanding_amount: num(record.outstanding_amount) ?? num(record.original_amount) ?? num(record.amount),
    description: str(record.description),
  };
}

const BUCKET_TONE: Record<AgingBucketKey, string> = {
  CURRENT: "ok",
  "1-30": "brass",
  "31-60": "warn",
  "61-90": "late",
  "90+": "bad",
};

export function AgingApplyBoard(props: AgingApplyBoardProps): JSX.Element {
  const {
    data,
    selectedBucket,
    onSelectBucket,
    applyRan,
    appliedIds,
    applyDecision,
    collectRan,
    collectionActions,
  } = props;
  const segments = agingSegments(data);
  const payment = featuredPayment(data);
  const invoices = competingInvoices(data, payment);
  const applied = appliedIds.length > 0;
  const bucketIds = selectedBucket ? invoiceIdsInBucket(data, selectedBucket) : [];
  return (
    <div className="pay-ar" aria-label="Customer cash">
      <div className="pay-aging">
        <div className="pay-aging-bar" role="list" aria-label="Invoice aging">
          {segments.map((seg) => (
            <button
              key={seg.key}
              type="button"
              role="listitem"
              className={`pay-aging-seg pay-aging-${BUCKET_TONE[seg.key]}${selectedBucket === seg.key ? " selected" : ""}`}
              style={{ width: `${seg.widthPct}%`, flexGrow: 0, flexShrink: 0, flexBasis: `${seg.widthPct}%` }}
              aria-pressed={selectedBucket === seg.key}
              aria-label={`${seg.key} ${formatAgingBucket(seg.key)}`}
              onClick={() => onSelectBucket(seg.key)}
            >
              <span className="mono pay-aging-key">{seg.key}</span>
              <span className="pay-aging-label">{formatAgingBucket(seg.key)}</span>
              <span className="num pay-aging-amt">{usd(seg.amount)}</span>
            </button>
          ))}
        </div>
        {selectedBucket ? (
          <div className="pay-aging-ids" aria-label={`${selectedBucket} invoices`}>
            {bucketIds.length ? (
              bucketIds.map((id) => (
                <span className="mono pay-chip" key={id}>
                  {id}
                </span>
              ))
            ) : (
              <span className="muted">No invoice ids in this bucket.</span>
            )}
          </div>
        ) : null}
      </div>
      <div className="pay-apply" aria-label="Cash application">
        <article className="doc-paper pay-tile">
          <div className="pay-sheet-kind">Payment</div>
          <div className="pay-sheet-vendor">{payment.payer_name}</div>
          <div className="mono pay-sheet-id">{payment.payment_id}</div>
          <div className="pay-field">
            <span className="pay-field-label">Amount</span>
            <span className="num">{usd(payment.amount)}</span>
          </div>
          <p className="pay-memo">“{payment.remittance_text}”</p>
        </article>
        <div className={applied ? "pay-gap snap" : "pay-gap"} aria-label={applied ? "Applied" : "Unmatched cash"}>
          {applyRan ? (
            applied ? (
              <span>{formatDecision(applyDecision)}</span>
            ) : (
              <span>More evidence required</span>
            )
          ) : (
            <span className="muted">Not applied</span>
          )}
        </div>
        <div className="pay-apply-invoices">
          {invoices.length ? (
            invoices.map((invoice) => (
              <article
                key={invoice.invoice_id}
                className={applied && appliedIds.includes(invoice.invoice_id) ? "doc-paper pay-tile applied" : "doc-paper pay-tile"}
              >
                <div className="pay-sheet-kind">Invoice</div>
                <div className="pay-sheet-vendor">{invoice.customer_name || "Customer"}</div>
                <div className="mono pay-sheet-id">{invoice.invoice_id}</div>
                <div className="pay-field">
                  <span className="pay-field-label">Open</span>
                  <span className="num">{usd(invoice.outstanding_amount)}</span>
                </div>
              </article>
            ))
          ) : (
            <article className="doc-paper pay-tile pay-sheet-missing">
              <div className="pay-sheet-kind">Open invoices</div>
              <p className="pay-missing">None returned</p>
            </article>
          )}
        </div>
      </div>
      {collectRan ? (
        <div className="pay-collect">
          <div className="pay-collect-chips">
            {collectionActions.length ? (
              collectionActions.map((chip) => (
                <span key={`${chip.action}-${chip.invoiceId || ""}`} className="pay-collect-chip">
                  <Pill tone={chip.draft ? "warn" : "neutral"}>{formatStatus(chip.action)}</Pill>
                  {chip.draft ? <span className="pay-draft">draft</span> : null}
                  {chip.invoiceId ? <span className="mono">{chip.invoiceId}</span> : null}
                </span>
              ))
            ) : (
              <span className="muted">No collection action returned.</span>
            )}
          </div>
          <p className="pay-collect-caption">Outbound mailbox is not attached on the live roster.</p>
        </div>
      ) : null}
    </div>
  );
}
