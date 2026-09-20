import { fireEvent, render, screen } from "@testing-library/react";
import {
  MatchBoard,
  computeJoins,
  railEntries,
  sheetsFromDetail,
} from "./MatchBoard";

const cleanDetail = {
  invoice_id: "INV-001",
  vendor: "Acme Supplies",
  amount: 12450,
  match_status: "matched",
  three_way: {
    artifacts: {
      invoice: { record: { invoice_id: "INV-001", vendor: "Acme Supplies", amount: 12450 } },
      purchase_order: { record: { po_id: "PO-101", vendor: "Acme Supplies", authorized_amount: 12450 } },
      goods_receipt: {
        record: { receipt_id: "GR-101", po_id: "PO-101", amount_received: 12450, quantity_ordered: 15, quantity_received: 15 },
      },
    },
  },
};

const qtyException = {
  invoice_id: "INV-003",
  vendor: "Datadog",
  amount: 15000,
  match_status: "exception",
  three_way: {
    artifacts: {
      invoice: { record: { invoice_id: "INV-003", vendor: "Datadog", amount: 15000 } },
      purchase_order: { record: { po_id: "PO-103", vendor: "Datadog", authorized_amount: 15000 } },
      goods_receipt: {
        record: { receipt_id: "GR-103", amount_received: 12000, quantity_ordered: 50, quantity_received: 40 },
      },
    },
  },
};

test("clean match joins amounts and qty", () => {
  const joins = computeJoins(sheetsFromDetail(cleanDetail));
  expect(joins).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ id: "amount-invoice-po", status: "match" }),
      expect.objectContaining({ id: "amount-po-gr", status: "match" }),
      expect.objectContaining({ id: "qty-po-gr", status: "match" }),
    ])
  );
});

test("INV-003 qty join is a mismatch and GR amount does not match", () => {
  const joins = computeJoins(sheetsFromDetail(qtyException));
  expect(joins.find((item) => item.id === "qty-po-gr")?.status).toBe("mismatch");
  expect(joins.find((item) => item.id === "amount-po-gr")?.status).toBe("mismatch");
  expect(joins.find((item) => item.id === "amount-invoice-po")?.status).toBe("match");
});

test("missing GR is a hollow slot", () => {
  const sheets = sheetsFromDetail({
    invoice_id: "INV-005",
    three_way: {
      artifacts: {
        invoice: { record: { invoice_id: "INV-005", vendor: "Figma", amount: 4375 } },
        purchase_order: { record: { po_id: "PO-108", vendor: "Figma", authorized_amount: 4375 } },
      },
    },
  });
  expect(sheets[2]?.present).toBe(false);
  render(<MatchBoard rows={[]} selectedId="INV-005" detail={{ invoice_id: "INV-005", three_way: { artifacts: { invoice: { record: { invoice_id: "INV-005", amount: 4375 } }, purchase_order: { record: { po_id: "PO-108", authorized_amount: 4375 } } } } }} decision="HOLD" onSelect={() => undefined} />);
  expect(screen.getByText("Missing")).toBeInTheDocument();
});

test("rail pins INV-001 Clean and keeps INV-003 selectable", () => {
  const entries = railEntries([], "INV-003");
  expect(entries[0]?.invoice_id).toBe("INV-001");
  expect(entries[0]?.pinned).toBe("Clean");
  expect(entries.some((row) => row.invoice_id === "INV-003")).toBe(true);
});

test("duplicate_peer renders overlapping copies", () => {
  render(
    <MatchBoard
      rows={[]}
      selectedId="INV-006"
      detail={{
        invoice_id: "INV-006",
        duplicate_peer: {
          document_a: { record: { invoice_id: "INV-006", vendor: "Shadow Vendor LLC", amount: 8750 } },
          document_b: { record: { invoice_id: "INV-007", vendor: "Shadow Vendor LLC", amount: 8750 } },
        },
      }}
      decision="HOLD"
      onSelect={() => undefined}
    />
  );
  expect(screen.getByLabelText("Duplicate vendor bills")).toBeInTheDocument();
  expect(screen.getAllByText("INV-006").length).toBeGreaterThan(0);
  expect(screen.getAllByText("INV-007").length).toBeGreaterThan(0);
});

test("clicking Clean calls onSelect with INV-001", () => {
  const onSelect = vi.fn();
  render(<MatchBoard rows={[]} selectedId="INV-003" detail={qtyException} decision="exception" onSelect={onSelect} />);
  fireEvent.click(screen.getByRole("button", { name: /Clean/i }));
  expect(onSelect).toHaveBeenCalledWith("INV-001");
});
