import { usd } from "../../api";
import { formatDecision, formatStatus } from "../../copy";
import { Pill } from "../../layout/Shell";
import {
  CLEAN_AP_ID,
  DEFAULT_AP_ID,
  artifactRecord,
  asList,
  isRecord,
  moneyEqual,
  num,
  qtyEqual,
  str,
} from "./pay-util";

export { CLEAN_AP_ID, DEFAULT_AP_ID };

export interface InvoiceRailRow {
  readonly invoice_id: string;
  readonly vendor?: string;
  readonly amount?: number;
  readonly match_status?: string;
  readonly duplicate_status?: string;
  readonly pinned?: string;
}

export type SheetKind = "invoice" | "po" | "gr";

export interface MatchSheet {
  readonly kind: SheetKind;
  readonly present: boolean;
  readonly title: string;
  readonly vendor?: string;
  readonly id?: string;
  readonly amount?: number;
  readonly qty?: number;
  readonly qtyOrdered?: number;
  readonly qtyReceived?: number;
}

export type JoinPair = "invoice-po" | "po-gr";
export type JoinField = "amount" | "qty";
export type JoinStatus = "match" | "mismatch";

export interface MatchJoin {
  readonly id: string;
  readonly pair: JoinPair;
  readonly field: JoinField;
  readonly status: JoinStatus;
}

export interface MatchBoardProps {
  readonly rows: readonly unknown[];
  readonly selectedId: string;
  readonly detail: unknown;
  readonly decision: string;
  readonly onSelect: (id: string) => void;
}

const SHEET_TITLE: Record<SheetKind, string> = {
  invoice: "Invoice",
  po: "Purchase order",
  gr: "Goods receipt",
};

const JOIN_X: Record<SheetKind, number> = {
  invoice: 16.7,
  po: 50,
  gr: 83.3,
};

const JOIN_Y: Record<JoinField, number> = {
  amount: 27,
  qty: 41,
};

export function parseRailRows(rows: readonly unknown[]): InvoiceRailRow[] {
  const parsed: InvoiceRailRow[] = [];
  for (const item of rows) {
    if (!isRecord(item)) {
      continue;
    }
    const id = str(item.invoice_id);
    if (!id) {
      continue;
    }
    parsed.push({
      invoice_id: id,
      vendor: str(item.vendor),
      amount: num(item.amount),
      match_status: str(item.match_status),
      duplicate_status: str(item.duplicate_status),
    });
  }
  return parsed;
}

export function railEntries(rows: readonly unknown[], selectedId: string): InvoiceRailRow[] {
  const parsed = parseRailRows(rows);
  const byId = new Map(parsed.map((row) => [row.invoice_id, row]));
  const featured: InvoiceRailRow[] = [];
  const clean = byId.get(CLEAN_AP_ID);
  featured.push({
    invoice_id: CLEAN_AP_ID,
    vendor: clean?.vendor,
    amount: clean?.amount,
    match_status: clean?.match_status,
    duplicate_status: clean?.duplicate_status,
    pinned: "Clean",
  });
  if (!byId.has(DEFAULT_AP_ID) && selectedId === DEFAULT_AP_ID) {
    featured.push({ invoice_id: DEFAULT_AP_ID });
  }
  for (const row of parsed) {
    if (row.invoice_id === CLEAN_AP_ID) {
      continue;
    }
    featured.push(row);
  }
  if (selectedId !== CLEAN_AP_ID && selectedId !== DEFAULT_AP_ID && !byId.has(selectedId)) {
    featured.push({ invoice_id: selectedId });
  }
  return featured;
}

function pickArtifact(...candidates: unknown[]): Record<string, unknown> | undefined {
  for (const candidate of candidates) {
    const record = artifactRecord(candidate);
    if (record) {
      return record;
    }
    if (isRecord(candidate) && (candidate.artifact_id || candidate.kind)) {
      return artifactRecord(candidate) || candidate;
    }
  }
  return undefined;
}

function qtyFrom(record: Record<string, unknown> | undefined): number | undefined {
  if (!record) {
    return undefined;
  }
  const direct = num(record.quantity) ?? num(record.qty) ?? num(record.billed_quantity);
  if (direct !== undefined) {
    return direct;
  }
  const lines = asList(record.lines);
  if (!lines.length) {
    return undefined;
  }
  let total = 0;
  let found = false;
  for (const line of lines) {
    if (!isRecord(line)) {
      continue;
    }
    const qty = num(line.quantity) ?? num(line.qty);
    if (qty !== undefined) {
      total += qty;
      found = true;
    }
  }
  return found ? total : undefined;
}

export function sheetsFromDetail(detail: unknown): readonly MatchSheet[] {
  const row = isRecord(detail) ? detail : {};
  const threeWay = isRecord(row.three_way) ? row.three_way : {};
  const artifacts = isRecord(threeWay.artifacts) ? threeWay.artifacts : {};
  const invoiceRec = pickArtifact(artifacts.invoice, row.source_document, row.invoice, row);
  const poRec = pickArtifact(artifacts.purchase_order, threeWay.purchase_order, row.po);
  const grRec = pickArtifact(artifacts.goods_receipt, threeWay.goods_receipt, row.goods_receipt);

  const invoice: MatchSheet = {
    kind: "invoice",
    present: Boolean(invoiceRec && (str(invoiceRec.invoice_id) || num(invoiceRec.amount) !== undefined || str(invoiceRec.vendor))),
    title: SHEET_TITLE.invoice,
    vendor: str(invoiceRec?.vendor) || str(row.vendor),
    id: str(invoiceRec?.invoice_id) || str(row.invoice_id),
    amount: num(invoiceRec?.amount) ?? num(row.amount),
    qty: qtyFrom(invoiceRec),
  };

  const po: MatchSheet = {
    kind: "po",
    present: Boolean(poRec && (str(poRec.po_id) || num(poRec.authorized_amount) !== undefined || str(poRec.vendor))),
    title: SHEET_TITLE.po,
    vendor: str(poRec?.vendor),
    id: str(poRec?.po_id),
    amount: num(poRec?.authorized_amount) ?? num(poRec?.amount),
    qty: qtyFrom(poRec) ?? num(poRec?.quantity_ordered),
  };

  const grPresent = Boolean(grRec && (str(grRec.receipt_id) || num(grRec.amount_received) !== undefined || num(grRec.quantity_received) !== undefined));
  const gr: MatchSheet = {
    kind: "gr",
    present: grPresent,
    title: SHEET_TITLE.gr,
    vendor: str(grRec?.vendor) || po.vendor,
    id: str(grRec?.receipt_id),
    amount: num(grRec?.amount_received) ?? num(grRec?.amount),
    qty: num(grRec?.quantity_received) ?? qtyFrom(grRec),
    qtyOrdered: num(grRec?.quantity_ordered),
    qtyReceived: num(grRec?.quantity_received),
  };

  return [invoice, po, gr];
}

export function duplicatePair(detail: unknown): { readonly a: Record<string, unknown>; readonly b: Record<string, unknown> } | undefined {
  if (!isRecord(detail) || !isRecord(detail.duplicate_peer)) {
    return undefined;
  }
  const peer = detail.duplicate_peer;
  const a = pickArtifact(peer.document_a);
  const b = pickArtifact(peer.document_b);
  if (!a && !b) {
    return undefined;
  }
  return { a: a || {}, b: b || {} };
}

export function computeJoins(sheets: readonly MatchSheet[]): readonly MatchJoin[] {
  const invoice = sheets.find((item) => item.kind === "invoice");
  const po = sheets.find((item) => item.kind === "po");
  const gr = sheets.find((item) => item.kind === "gr");
  const joins: MatchJoin[] = [];
  pushAmountJoin(joins, "invoice-po", invoice, po);
  pushAmountJoin(joins, "po-gr", po, gr);
  const poQty = po?.present ? po.qty ?? gr?.qtyOrdered : undefined;
  const grQty = gr?.present ? gr.qtyReceived ?? gr.qty : undefined;
  pushQtyJoin(joins, "invoice-po", invoice?.present ? invoice.qty : undefined, po?.present ? po.qty : undefined);
  pushQtyJoin(joins, "po-gr", poQty, grQty);
  return joins;
}

function pushAmountJoin(
  joins: MatchJoin[],
  pair: JoinPair,
  left: MatchSheet | undefined,
  right: MatchSheet | undefined
): void {
  if (!left?.present || !right?.present) {
    return;
  }
  if (left.amount === undefined || right.amount === undefined) {
    return;
  }
  joins.push({
    id: `amount-${pair}`,
    pair,
    field: "amount",
    status: moneyEqual(left.amount, right.amount) ? "match" : "mismatch",
  });
}

function pushQtyJoin(joins: MatchJoin[], pair: JoinPair, left: number | undefined, right: number | undefined): void {
  if (left === undefined || right === undefined) {
    return;
  }
  joins.push({
    id: `qty-${pair}`,
    pair,
    field: "qty",
    status: qtyEqual(left, right) ? "match" : "mismatch",
  });
}

function sheetFromRecord(kind: SheetKind, record: Record<string, unknown>): MatchSheet {
  return {
    kind,
    present: true,
    title: SHEET_TITLE[kind],
    vendor: str(record.vendor),
    id: str(record.invoice_id) || str(record.po_id) || str(record.receipt_id) || str(record.vendor_invoice_number),
    amount: num(record.amount) ?? num(record.authorized_amount) ?? num(record.amount_received),
    qty: qtyFrom(record),
  };
}

function JoinOverlay(props: { joins: readonly MatchJoin[] }): JSX.Element {
  const { joins } = props;
  return (
    <svg className="pay-joins" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="false">
      {joins.map((join) => {
        const [fromKind, toKind] = join.pair.split("-") as [SheetKind, SheetKind];
        const y = JOIN_Y[join.field];
        const x1 = JOIN_X[fromKind] + 12;
        const x2 = JOIN_X[toKind] - 12;
        const mid = (x1 + x2) / 2;
        const d =
          join.status === "match"
            ? `M ${x1} ${y} L ${x2} ${y}`
            : `M ${x1} ${y} L ${mid - 4} ${y} M ${mid + 4} ${y} L ${x2} ${y}`;
        return (
          <path
            key={join.id}
            className={`pay-join pay-join-${join.status} pay-join-${join.field}`}
            d={d}
            aria-label={`${join.field} ${join.pair} ${join.status}`}
          />
        );
      })}
    </svg>
  );
}

function SheetCard(props: { sheet: MatchSheet }): JSX.Element {
  const { sheet } = props;
  if (!sheet.present) {
    return (
      <article className="doc-paper pay-sheet pay-sheet-missing">
        <div className="pay-sheet-kind">{sheet.title}</div>
        <p className="pay-missing">Missing</p>
      </article>
    );
  }
  const qtyLabel = qtyLabelFor(sheet);
  return (
    <article className="doc-paper pay-sheet">
      <div className="pay-sheet-kind">{sheet.title}</div>
      <div className="pay-sheet-vendor">{sheet.vendor || "—"}</div>
      <div className="mono pay-sheet-id">{sheet.id || "—"}</div>
      <div className="pay-field pay-field-amount">
        <span className="pay-field-label">Amount</span>
        <span className="num">{usd(sheet.amount)}</span>
      </div>
      <div className="pay-field pay-field-qty">
        <span className="pay-field-label">Qty</span>
        <span className="num">{qtyLabel}</span>
      </div>
    </article>
  );
}

function qtyLabelFor(sheet: MatchSheet): string {
  if (sheet.kind === "gr" && sheet.qtyOrdered !== undefined && sheet.qtyReceived !== undefined) {
    return `${sheet.qtyReceived} received / ${sheet.qtyOrdered} ordered`;
  }
  if (sheet.qty !== undefined) {
    return String(sheet.qty);
  }
  if (sheet.qtyReceived !== undefined) {
    return String(sheet.qtyReceived);
  }
  return "—";
}

function DuplicateStage(props: {
  a: Record<string, unknown>;
  b: Record<string, unknown>;
  decision: string;
}): JSX.Element {
  const { a, b, decision } = props;
  return (
    <div className="pay-dup" aria-label="Duplicate vendor bills">
      <SheetCard sheet={sheetFromRecord("invoice", a)} />
      <SheetCard sheet={sheetFromRecord("invoice", b)} />
      <div className="pay-stamp pay-stamp-dup">
        <Pill tone="bad">{stampLabel(decision)}</Pill>
      </div>
    </div>
  );
}

export function MatchBoard(props: MatchBoardProps): JSX.Element {
  const { rows, selectedId, detail, decision, onSelect } = props;
  const entries = railEntries(rows || [], selectedId);
  const pair = duplicatePair(detail);
  const sheets = sheetsFromDetail(detail);
  const joins = pair ? [] : computeJoins(sheets);
  return (
    <div className="pay-match" aria-label="Three-way match">
      <aside className="pay-rail" aria-label="Invoice register">
        {entries.map((row) => {
          const selected = row.invoice_id === selectedId;
          const label = [row.pinned, row.vendor, row.invoice_id].filter(Boolean).join(" ");
          return (
            <button
              key={row.invoice_id}
              type="button"
              className={selected ? "pay-rail-item selected" : "pay-rail-item"}
              aria-pressed={selected}
              aria-label={label}
              onClick={() => onSelect(row.invoice_id)}
            >
              {row.pinned ? <span className="pay-pin">{row.pinned}</span> : null}
              <span className="pay-rail-vendor">{row.vendor || row.invoice_id}</span>
              <span className="mono pay-rail-id">{row.invoice_id}</span>
              <span className="num pay-rail-amt">{usd(row.amount)}</span>
            </button>
          );
        })}
      </aside>
      <div className="pay-stage">
        <div className="pay-stamp">
          <span className={`pill pay-stamp-pill ${decisionTone(decision)}`}>{stampLabel(decision)}</span>
        </div>
        {pair ? (
          <DuplicateStage a={pair.a} b={pair.b} decision={decision} />
        ) : (
          <div className="pay-sheets">
            {sheets.map((sheet) => (
              <SheetCard key={sheet.kind} sheet={sheet} />
            ))}
            <JoinOverlay joins={joins} />
          </div>
        )}
        {isRecord(detail) && str(detail.duplicate_status) === "duplicate" && !pair ? (
          <p className="pay-dup-note">{formatStatus("duplicate")}</p>
        ) : null}
      </div>
    </div>
  );
}

function stampLabel(decision: string): string {
  const token = decision.trim();
  const upper = token.toUpperCase();
  if (
    upper === "APPROVE" ||
    upper === "HOLD" ||
    upper === "REJECT" ||
    upper === "AUTO_APPLY" ||
    upper === "HUMAN_REVIEW" ||
    upper === "UNAPPLIED"
  ) {
    return formatDecision(token);
  }
  return formatStatus(token);
}

function decisionTone(decision: string): string {
  const value = decision.toLowerCase();
  if (value.includes("approve") || value === "matched") {
    return "ok";
  }
  if (value.includes("hold") || value.includes("reject") || value.includes("exception") || value.includes("duplicate")) {
    return "bad";
  }
  return "neutral";
}
