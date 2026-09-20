import { usd } from "../../api";

export interface WaterfallStep {
  readonly id: string;
  readonly caption: string;
  readonly sign: "+" | "−" | "=" | "vs";
  readonly amount: number;
  readonly role: "flow" | "expected" | "deposit";
}

export interface StripeWaterfallProps {
  readonly breakdown?: unknown;
  readonly deposit?: number | null;
  readonly tied?: boolean;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
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

export function waterfallSteps(breakdown: unknown, deposit: number | null | undefined): readonly WaterfallStep[] {
  const row = isRecord(breakdown) ? breakdown : {};
  const charges = readNumber(row.gross_payments);
  const refunds = readNumber(row.refunds);
  const disputes = readNumber(row.chargebacks);
  const fees = readNumber(row.fees);
  const expected =
    readOptionalNumber(row.expected_payout) ?? readOptionalNumber(row.net) ?? 0;
  const bank = deposit ?? readOptionalNumber(row.bank_deposit_amount) ?? 0;
  return [
    { id: "charges", caption: "+ charges", sign: "+", amount: charges, role: "flow" },
    { id: "refunds", caption: "− refunds", sign: "−", amount: refunds, role: "flow" },
    { id: "disputes", caption: "− disputes / chargebacks", sign: "−", amount: disputes, role: "flow" },
    { id: "fees", caption: "− fees", sign: "−", amount: fees, role: "flow" },
    { id: "expected", caption: "= expected payout", sign: "=", amount: expected, role: "expected" },
    { id: "deposit", caption: "vs bank deposit", sign: "vs", amount: bank, role: "deposit" },
  ];
}

function barWidthPct(amount: number, scale: number): number {
  if (!(scale > 0)) {
    return 0;
  }
  return Math.min(100, (Math.abs(amount) / scale) * 100);
}

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function FlowBar(props: { step: WaterfallStep; scale: number }): JSX.Element {
  const { step, scale } = props;
  const width = barWidthPct(step.amount, scale);
  return (
    <div className="cash-waterfall-step">
      <div className="cash-waterfall-caption">{step.caption}</div>
      <div className="cash-waterfall-track">
        <div
          className={cx("cash-waterfall-bar", `cash-waterfall-bar-${step.id}`)}
          style={{ width: `${width}%` }}
        />
      </div>
      <div className="mono cash-waterfall-amt">{usd(Math.abs(step.amount))}</div>
    </div>
  );
}

function CompareBars(props: {
  expected: WaterfallStep;
  deposit: WaterfallStep;
  scale: number;
  tied: boolean;
}): JSX.Element {
  const { expected, deposit, scale, tied } = props;
  const expectedAbs = Math.abs(expected.amount);
  const depositAbs = Math.abs(deposit.amount);
  const shared = Math.min(expectedAbs, depositAbs);
  const expectedExtra = Math.max(0, expectedAbs - depositAbs);
  const depositExtra = Math.max(0, depositAbs - expectedAbs);
  const mismatch = expectedExtra > 0.005 || depositExtra > 0.005;
  return (
    <div className="cash-waterfall-compare">
      <div className="cash-waterfall-step">
        <div className="cash-waterfall-caption">{expected.caption}</div>
        <div className="cash-waterfall-track">
          <div
            className={cx("cash-waterfall-bar", "cash-waterfall-bar-expected", tied && !mismatch && "is-tied")}
            style={{ width: `${barWidthPct(shared, scale)}%` }}
          />
          {expectedExtra > 0.005 ? (
            <div
              className="cash-waterfall-bar cash-waterfall-overhang"
              style={{ width: `${barWidthPct(expectedExtra, scale)}%` }}
            />
          ) : null}
        </div>
        <div className="mono cash-waterfall-amt">{usd(expected.amount)}</div>
      </div>
      <div className="cash-waterfall-step">
        <div className="cash-waterfall-caption">{deposit.caption}</div>
        <div className="cash-waterfall-track">
          <div
            className={cx("cash-waterfall-bar", "cash-waterfall-bar-deposit", tied && !mismatch && "is-tied")}
            style={{ width: `${barWidthPct(shared, scale)}%` }}
          />
          {depositExtra > 0.005 ? (
            <div
              className="cash-waterfall-bar cash-waterfall-overhang"
              style={{ width: `${barWidthPct(depositExtra, scale)}%` }}
            />
          ) : null}
        </div>
        <div className="mono cash-waterfall-amt">{usd(deposit.amount)}</div>
      </div>
    </div>
  );
}

export function StripeWaterfall(props: StripeWaterfallProps): JSX.Element {
  const steps = waterfallSteps(props.breakdown, props.deposit);
  const flow = steps.filter((step) => step.role === "flow");
  const expected = steps.find((step) => step.role === "expected");
  const deposit = steps.find((step) => step.role === "deposit");
  const scale = Math.max(...steps.map((step) => Math.abs(step.amount)), 1);
  const tied = Boolean(props.tied) && Boolean(expected && deposit && Math.abs(expected.amount - deposit.amount) < 0.005);

  return (
    <div className="cash-waterfall" role="img" aria-label="Stripe payout waterfall">
      {flow.map((step) => (
        <FlowBar key={step.id} step={step} scale={scale} />
      ))}
      {expected && deposit ? (
        <CompareBars expected={expected} deposit={deposit} scale={scale} tied={tied} />
      ) : null}
    </div>
  );
}
