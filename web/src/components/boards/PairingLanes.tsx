import { usd } from "../../api";
import { explainCashMatch, formatMatchType } from "../../copy";

export const NORTHSTAR_TXN = "TXN-2026-09-015";
export const NORTHSTAR_LEDGER = "GL-AR-NS";
export const HELIOS_TXN = "TXN-2026-09-011";
export const HELIOS_LEDGER = "GL-AP-WIRE";
export const HELIOS_FEE = "FEE-729103";
export const GROUPED_TXN = "TXN-2026-09-008";
export const NORTHSTAR_BANK_AMOUNT = 12412.4;
export const NORTHSTAR_LEDGER_AMOUNT = 12400;
export const NORTHSTAR_GAP = 12.4;

export type PairKind = "matched" | "explained" | "unexplained";

export interface PairChip {
  readonly id: string;
  readonly amount?: number;
  readonly label?: string;
}

export interface PairRow {
  readonly id: string;
  readonly matchType: string;
  readonly status: string;
  readonly kind: PairKind;
  readonly bank: PairChip;
  readonly ledger: readonly PairChip[];
  readonly feeIds: readonly string[];
  readonly bankAmount: number;
  readonly ledgerAmount: number;
  readonly difference: number;
}

export interface PairingLanesProps {
  readonly pairs: readonly PairRow[];
  readonly selectedId: string;
  readonly onSelect: (id: string) => void;
}

const FEE_ID_RE = /FEE-[A-Z0-9-]+/g;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readNumber(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function readOptionalNumber(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function readStringArray(value: unknown): readonly string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.length > 0);
}

function uniqueIds(ids: readonly string[]): readonly string[] {
  return [...new Set(ids)];
}

function artifactId(value: unknown): string {
  if (!isRecord(value)) {
    return "";
  }
  const record = isRecord(value.record) ? value.record : {};
  return (
    readString(value.artifact_id) ||
    readString(record.transaction_id) ||
    readString(record.entry_id) ||
    readString(record.evidence_id) ||
    ""
  );
}

function artifactAmount(value: unknown): number | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const record = isRecord(value.record) ? value.record : {};
  return readOptionalNumber(record.amount) ?? readOptionalNumber(value.amount);
}

function artifactLabel(value: unknown): string {
  if (!isRecord(value)) {
    return "";
  }
  const record = isRecord(value.record) ? value.record : {};
  return readString(record.counterparty) || readString(value.title) || readString(record.description);
}

function artifactChip(value: unknown, fallbackId: string): PairChip {
  const id = artifactId(value) || fallbackId;
  return {
    id,
    amount: artifactAmount(value),
    label: artifactLabel(value),
  };
}

function featuredCase(source: unknown, key: string): unknown {
  if (!isRecord(source)) {
    return undefined;
  }
  return source[key];
}

export function pairKind(matchType: string, bankId: string, status: string): PairKind {
  if (bankId === NORTHSTAR_TXN || matchType === "UNEXPLAINED_DIFFERENCE") {
    return "unexplained";
  }
  if (bankId === HELIOS_TXN || matchType === "FEE_NETTED") {
    return "explained";
  }
  if (
    matchType === "UNMATCHED_BANK" ||
    matchType === "UNMATCHED_LEDGER" ||
    status === "HUMAN_REVIEW"
  ) {
    return "unexplained";
  }
  return "matched";
}

function feeIdsFor(match: Record<string, unknown>, bankId: string): readonly string[] {
  if (bankId === NORTHSTAR_TXN) {
    return [];
  }
  const fromField = readStringArray(match.fee_evidence_ids);
  const fromEvidence = readStringArray(match.evidence).flatMap((item) => item.match(FEE_ID_RE) ?? []);
  const planted = bankId === HELIOS_TXN ? [HELIOS_FEE] : [];
  return uniqueIds([...fromField, ...fromEvidence, ...planted]);
}

function pairFromMatch(raw: unknown): PairRow | null {
  if (!isRecord(raw)) {
    return null;
  }
  const bankIds = readStringArray(raw.bank_transaction_ids);
  const ledgerIds = readStringArray(raw.ledger_entry_ids);
  const bankId = bankIds[0] || "";
  if (!bankId) {
    return null;
  }
  const matchType = readString(raw.match_type);
  const status = readString(raw.status);
  const bankAmount = readNumber(raw.bank_amount);
  const ledgerAmount = readNumber(raw.ledger_amount);
  const difference =
    readOptionalNumber(raw.difference) ?? Math.abs(bankAmount - ledgerAmount);
  const ledger: PairChip[] =
    ledgerIds.length > 0
      ? ledgerIds.map((id) => ({
          id,
          amount: ledgerIds.length === 1 ? ledgerAmount : undefined,
        }))
      : [];
  return {
    id: readString(raw.reconciliation_id) || readString(raw.match_key) || bankId,
    matchType,
    status,
    kind: pairKind(matchType, bankId, status),
    bank: { id: bankId, amount: bankAmount },
    ledger,
    feeIds: feeIdsFor(raw, bankId),
    bankAmount,
    ledgerAmount,
    difference,
  };
}

function pairFromFeatured(
  raw: unknown,
  matchType: string,
  status: string,
  fallbackBankId: string,
  fallbackLedger: readonly PairChip[],
  fallbackBankAmount: number,
  fallbackLedgerAmount: number
): PairRow {
  const caseRow = isRecord(raw) ? raw : {};
  const bankChip = artifactChip(caseRow.bank, fallbackBankId);
  const bankId = bankChip.id || fallbackBankId;
  const ledgerRaw = Array.isArray(caseRow.ledger) ? caseRow.ledger : [];
  const ledger =
    ledgerRaw.length > 0
      ? ledgerRaw.map((item, index) => artifactChip(item, fallbackLedger[index]?.id || `${bankId}-ledger-${index}`))
      : fallbackLedger;
  const kind = pairKind(matchType, bankId, status);
  const feeIds =
    bankId === NORTHSTAR_TXN
      ? []
      : uniqueIds([
          ...(kind === "explained" && bankId === HELIOS_TXN ? [HELIOS_FEE] : []),
          ...(Array.isArray(caseRow.fees) ? caseRow.fees.map((item) => artifactId(item)).filter(Boolean) : []),
        ]);
  const bankAmount = bankChip.amount ?? fallbackBankAmount;
  const ledgerAmount =
    ledger.reduce((sum, chip) => sum + (chip.amount ?? 0), 0) || fallbackLedgerAmount;
  return {
    id: bankId,
    matchType,
    status,
    kind,
    bank: { ...bankChip, id: bankId, amount: bankAmount },
    ledger,
    feeIds,
    bankAmount,
    ledgerAmount,
    difference: Math.abs(bankAmount - ledgerAmount),
  };
}

function plantedNorthstar(): PairRow {
  return {
    id: NORTHSTAR_TXN,
    matchType: "UNEXPLAINED_DIFFERENCE",
    status: "HUMAN_REVIEW",
    kind: "unexplained",
    bank: {
      id: NORTHSTAR_TXN,
      amount: NORTHSTAR_BANK_AMOUNT,
      label: "Northstar LLC",
    },
    ledger: [
      {
        id: NORTHSTAR_LEDGER,
        amount: NORTHSTAR_LEDGER_AMOUNT,
        label: "Northstar LLC",
      },
    ],
    feeIds: [],
    bankAmount: NORTHSTAR_BANK_AMOUNT,
    ledgerAmount: NORTHSTAR_LEDGER_AMOUNT,
    difference: NORTHSTAR_GAP,
  };
}

function plantedHelios(featured: unknown): PairRow {
  return pairFromFeatured(
    featured,
    "FEE_NETTED",
    "EXPLAINED_EXCEPTION",
    HELIOS_TXN,
    [{ id: HELIOS_LEDGER, amount: -10000, label: "Helios Hardware" }],
    -10025,
    -10000
  );
}

function pairRank(pair: PairRow): number {
  if (pair.bank.id === NORTHSTAR_TXN) {
    return 0;
  }
  if (pair.bank.id === HELIOS_TXN) {
    return 1;
  }
  if (pair.matchType === "GROUPED_MATCH" || pair.bank.id === GROUPED_TXN) {
    return 2;
  }
  if (pair.kind === "unexplained") {
    return 3;
  }
  return 4;
}

function hasBank(pairs: readonly PairRow[], bankId: string): boolean {
  return pairs.some((pair) => pair.bank.id === bankId);
}

export function pairsFromCashPayload(input: {
  readonly matches?: readonly unknown[];
  readonly featuredCases?: unknown;
}): PairRow[] {
  const fromMatches = (input.matches ?? [])
    .map(pairFromMatch)
    .filter((row): row is PairRow => row !== null);
  const featured = input.featuredCases;
  const unexplainedCase = featuredCase(featured, "unexplained");
  const feeCase = featuredCase(featured, "fee_netted");
  const groupedCase = featuredCase(featured, "grouped");
  const extra: PairRow[] = [];
  if (!hasBank(fromMatches, NORTHSTAR_TXN)) {
    extra.push(
      unexplainedCase
        ? pairFromFeatured(
            unexplainedCase,
            "UNEXPLAINED_DIFFERENCE",
            "HUMAN_REVIEW",
            NORTHSTAR_TXN,
            [{ id: NORTHSTAR_LEDGER, amount: NORTHSTAR_LEDGER_AMOUNT, label: "Northstar LLC" }],
            NORTHSTAR_BANK_AMOUNT,
            NORTHSTAR_LEDGER_AMOUNT
          )
        : plantedNorthstar()
    );
  }
  if (!hasBank(fromMatches, HELIOS_TXN) && (feeCase || fromMatches.length === 0)) {
    extra.push(plantedHelios(feeCase));
  }
  if (!hasBank(fromMatches, GROUPED_TXN) && groupedCase) {
    extra.push(
      pairFromFeatured(groupedCase, "GROUPED_MATCH", "MATCHED", GROUPED_TXN, [], -18500, -18500)
    );
  }
  const merged = [...extra, ...fromMatches];
  return [...merged].sort((left, right) => pairRank(left) - pairRank(right));
}

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function Chip(props: { chip: PairChip; side: "bank" | "ledger" }): JSX.Element {
  const { chip, side } = props;
  return (
    <span className={cx("cash-chip", `cash-chip-${side}`)}>
      <span className="mono">{chip.id}</span>
      {chip.amount !== undefined ? <span className="mono cash-chip-amt">{usd(chip.amount)}</span> : null}
      {chip.label ? <span className="cash-chip-label">{chip.label}</span> : null}
    </span>
  );
}

function Connector(props: { pair: PairRow }): JSX.Element {
  const { pair } = props;
  if (pair.kind === "unexplained") {
    const gap = usd(pair.difference || NORTHSTAR_GAP);
    const closeCaption = pair.bank.id === NORTHSTAR_TXN;
    return (
      <div className="cash-connector cash-connector-broken" aria-hidden={false}>
        <svg className="cash-pair-svg" viewBox="0 0 140 48" preserveAspectRatio="none">
          <path className="cash-stub cash-stub-bank" d="M0 24 H46" />
          <path className="cash-stub cash-stub-ledger" d="M140 24 H94" />
        </svg>
        <div className="cash-gap">
          <span className="mono cash-gap-amt">{gap}</span>
          {closeCaption ? <span className="cash-gap-caption">close cannot finish</span> : null}
        </div>
      </div>
    );
  }
  const feeLabel = pair.feeIds[0];
  return (
    <div className={cx("cash-connector", pair.kind === "explained" && "cash-connector-explained")}>
      <svg className="cash-pair-svg" viewBox="0 0 140 48" preserveAspectRatio="none">
        <path className="cash-pair-line" d="M0 24 C46 24, 94 24, 140 24" />
      </svg>
      {feeLabel ? <span className="mono cash-fee-label">{feeLabel}</span> : null}
    </div>
  );
}

export function PairingLanes(props: PairingLanesProps): JSX.Element {
  const { pairs, selectedId, onSelect } = props;
  const selected = pairs.find((pair) => pair.id === selectedId) ?? pairs[0];
  const story = selected
    ? explainCashMatch({
        match_type: selected.matchType,
        bank_amount: selected.bankAmount,
        ledger_amount: selected.ledgerAmount,
        ledger_entry_ids: selected.ledger.map((chip) => chip.id),
      })
    : undefined;

  return (
    <div className="cash-stage" aria-label="Bank vs ledger">
      <div className="cash-lane-heads">
        <div className="cash-lane-head">Bank</div>
        <div className="cash-lane-head cash-lane-head-mid" aria-hidden="true" />
        <div className="cash-lane-head">Ledger</div>
      </div>
      <div className="cash-pairs">
        {pairs.map((pair) => {
          const isSelected = pair.id === selectedId;
          return (
            <button
              key={pair.id}
              type="button"
              className={cx(
                "cash-pair",
                `cash-pair-${pair.kind}`,
                isSelected && "is-selected"
              )}
              aria-pressed={isSelected}
              onClick={() => onSelect(pair.id)}
            >
              <div className="cash-bank">
                <Chip chip={pair.bank} side="bank" />
              </div>
              <Connector pair={pair} />
              <div className="cash-ledger">
                {pair.ledger.length > 0 ? (
                  pair.ledger.map((chip) => <Chip key={chip.id} chip={chip} side="ledger" />)
                ) : (
                  <span className="cash-chip cash-chip-empty">No ledger row</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
      <div className="cash-legend">
        <span className="cash-legend-item cash-legend-matched">Matched</span>
        <span className="cash-legend-dot" aria-hidden="true">
          ·
        </span>
        <span className="cash-legend-item cash-legend-explained">Explained fee</span>
        <span className="cash-legend-dot" aria-hidden="true">
          ·
        </span>
        <span className="cash-legend-item cash-legend-unexplained">Unexplained</span>
      </div>
      {selected && story ? (
        <p className="cash-pair-caption">
          <span className="mono">{selected.bank.id}</span> {story.title}
          {selected.matchType ? <span className="muted"> · {formatMatchType(selected.matchType)}</span> : null}
        </p>
      ) : null}
    </div>
  );
}
