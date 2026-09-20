import { fireEvent, render, screen } from "@testing-library/react";
import {
  HELIOS_FEE,
  HELIOS_TXN,
  NORTHSTAR_TXN,
  PairingLanes,
  pairsFromCashPayload,
  type PairRow,
} from "./PairingLanes";

function samplePairs(): PairRow[] {
  return pairsFromCashPayload({
    matches: [],
    featuredCases: {
      unexplained: {
        bank: {
          artifact_id: NORTHSTAR_TXN,
          record: { transaction_id: NORTHSTAR_TXN, amount: 12412.4, counterparty: "Northstar LLC" },
        },
        ledger: [{ artifact_id: "GL-AR-NS", record: { entry_id: "GL-AR-NS", amount: 12400 } }],
        fees: [{ artifact_id: "FEE-SHOULD-NOT-RENDER" }],
      },
      fee_netted: {
        bank: {
          artifact_id: HELIOS_TXN,
          record: { transaction_id: HELIOS_TXN, amount: -10025, counterparty: "Helios Hardware" },
        },
        ledger: [{ artifact_id: "GL-AP-WIRE", record: { entry_id: "GL-AP-WIRE", amount: -10000 } }],
        fees: [{ artifact_id: HELIOS_FEE }],
      },
    },
  });
}

test("empty matches still plant the Northstar $12.40 gap", () => {
  const pairs = pairsFromCashPayload({ matches: [] });
  expect(pairs.some((pair) => pair.bank.id === NORTHSTAR_TXN)).toBe(true);
  const northstar = pairs.find((pair) => pair.bank.id === NORTHSTAR_TXN);
  expect(northstar?.kind).toBe("unexplained");
  expect(northstar?.feeIds).toEqual([]);
  expect(northstar?.difference).toBeCloseTo(12.4);
});

test("Northstar featured fees are ignored", () => {
  const pairs = samplePairs();
  const northstar = pairs.find((pair) => pair.bank.id === NORTHSTAR_TXN);
  expect(northstar?.feeIds).not.toContain("FEE-SHOULD-NOT-RENDER");
  expect(northstar?.feeIds).not.toContain(HELIOS_FEE);
});

test("lanes render the broken $12.40 gap and the Helios fee on its line", () => {
  const pairs = samplePairs();
  const { container } = render(
    <PairingLanes pairs={pairs} selectedId={NORTHSTAR_TXN} onSelect={() => undefined} />
  );
  expect(screen.getByLabelText("Bank vs ledger")).toBeInTheDocument();
  expect(screen.getByText("Bank")).toBeInTheDocument();
  expect(screen.getByText("Ledger")).toBeInTheDocument();
  expect(container.textContent).toMatch(/12\.40/);
  expect(container.querySelector(".cash-stub")).not.toBeNull();
  expect(container.querySelector(".cash-pair-unexplained.is-selected")).not.toBeNull();
  expect(screen.getByText(HELIOS_FEE)).toBeInTheDocument();
  const northstar = screen.getByRole("button", { name: /TXN-2026-09-015/i });
  expect(northstar.textContent).not.toContain(HELIOS_FEE);
});

test("clicking Helios re-targets selection", () => {
  const pairs = samplePairs();
  const onSelect = vi.fn();
  render(<PairingLanes pairs={pairs} selectedId={NORTHSTAR_TXN} onSelect={onSelect} />);
  fireEvent.click(screen.getByRole("button", { name: /TXN-2026-09-011/i }));
  expect(onSelect).toHaveBeenCalledWith(HELIOS_TXN);
});
