import { fireEvent, render, screen } from "@testing-library/react";
import { AgingApplyBoard, agingSegments, competingInvoices, featuredPayment, invoiceIdsInBucket } from "./AgingApplyBoard";
import { collectionBlockReason } from "./pay-util";

const sample = {
  outstanding: 10000,
  buckets: { CURRENT: 5000, "1-30": 2000, "31-60": 1500, "61-90": 1000, "90+": 500 },
  aging_lines: [
    { invoice_id: "INV-AR-010", aging_bucket: "CURRENT" },
    { invoice_id: "INV-AR-011", aging_bucket: "CURRENT" },
  ],
  invoices: [
    { invoice_id: "INV-AR-010", customer_name: "Lumen Labs", outstanding_amount: 5000, aging_bucket: "CURRENT" },
    { invoice_id: "INV-AR-011", customer_name: "Lumen Labs", outstanding_amount: 5000, aging_bucket: "CURRENT" },
  ],
  payments: [
    {
      payment_id: "PAY-004",
      payer_name: "Lumen Labs",
      amount: 5000,
      remittance_text: "September billing",
    },
  ],
};

test("aging segments use outstanding for width", () => {
  const segs = agingSegments(sample);
  expect(segs[0]?.key).toBe("CURRENT");
  expect(segs[0]?.widthPct).toBe(50);
  expect(segs[4]?.key).toBe("90+");
  expect(segs[4]?.widthPct).toBe(5);
});

test("zero outstanding does not divide by zero", () => {
  const segs = agingSegments({ outstanding: 0, buckets: {} });
  expect(segs).toHaveLength(5);
  expect(segs.every((item) => item.widthPct === 20)).toBe(true);
});

test("bucket click lists API invoice ids only", () => {
  expect(invoiceIdsInBucket(sample, "CURRENT")).toEqual(["INV-AR-010", "INV-AR-011"]);
  expect(invoiceIdsInBucket(sample, "90+")).toEqual([]);
});

test("featured payment falls back to PAY-004 labels when fields are missing", () => {
  const payment = featuredPayment({});
  expect(payment.payment_id).toBe("PAY-004");
  expect(payment.payer_name).toBe("Lumen Labs");
  expect(payment.amount).toBe(5000);
  expect(payment.remittance_text).toBe("September billing");
});

test("competing invoices come from API rows", () => {
  const invoices = competingInvoices(sample, featuredPayment(sample));
  expect(invoices.map((item) => item.invoice_id)).toEqual(["INV-AR-010", "INV-AR-011"]);
});

test("render shows CURRENT and a refused apply gap after a failed apply", () => {
  render(
    <AgingApplyBoard
      data={sample}
      selectedBucket={null}
      onSelectBucket={() => undefined}
      applyRan={true}
      appliedIds={[]}
      applyDecision="HUMAN_REVIEW"
      collectRan={false}
      collectionActions={[]}
    />
  );
  expect(screen.getByText("CURRENT")).toBeInTheDocument();
  expect(screen.getByText("More evidence required")).toBeInTheDocument();
  expect(screen.queryByText(/AUTO_APPLY/i)).not.toBeInTheDocument();
});

test("collect chips mark SEND as draft and do not say email sent", () => {
  const { container } = render(
    <AgingApplyBoard
      data={sample}
      selectedBucket={null}
      onSelectBucket={() => undefined}
      applyRan={false}
      appliedIds={[]}
      applyDecision="not run"
      collectRan={true}
      collectionActions={[{ action: "SEND_OVERDUE_REMINDER", invoiceId: "INV-AR-014", draft: true }]}
    />
  );
  expect(screen.getByText(/draft/i)).toBeInTheDocument();
  expect(screen.getByText("Outbound mailbox is not attached on the live roster.")).toBeInTheDocument();
  expect(container.textContent?.toLowerCase()).not.toMatch(/email sent/);
  expect(container.textContent?.toLowerCase()).not.toMatch(/sent the collection/);
});

test("collectionBlockReason reads Kernel blocked copy", () => {
  expect(
    collectionBlockReason({
      result: { result: { blocked: true, block_reason: "Handle apply first." } },
    })
  ).toBe("Handle apply first.");
  expect(collectionBlockReason({ result: { decisions: [] } })).toBeUndefined();
});

test("collect blocked reason is Kernel copy, not a send", () => {
  const { container } = render(
    <AgingApplyBoard
      data={sample}
      selectedBucket={null}
      onSelectBucket={() => undefined}
      applyRan={false}
      appliedIds={[]}
      applyDecision="not run"
      collectRan={true}
      collectionActions={[]}
      collectionNote="Apply has not drained new deposits for this as-of."
    />
  );
  expect(screen.getByText(/Apply has not drained new deposits/i)).toBeInTheDocument();
  expect(container.textContent?.toLowerCase()).not.toMatch(/email sent/);
});

test("clicking CURRENT lists invoice id chips", () => {
  const onSelectBucket = vi.fn();
  render(
    <AgingApplyBoard
      data={sample}
      selectedBucket="CURRENT"
      onSelectBucket={onSelectBucket}
      applyRan={false}
      appliedIds={[]}
      applyDecision="not run"
      collectRan={false}
      collectionActions={[]}
    />
  );
  expect(screen.getAllByText("INV-AR-010").length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole("listitem", { name: /CURRENT/ }));
  expect(onSelectBucket).toHaveBeenCalledWith("CURRENT");
});
