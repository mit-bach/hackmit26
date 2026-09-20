import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CoverageGrid } from "../components/CoverageGrid";
import Coverage from "./Coverage";

function renderCoverage(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <Coverage />
    </MemoryRouter>,
  );
}

test("coverage wall includes required capability ids", () => {
  renderCoverage();
  expect(screen.getByRole("button", { name: /ap\.self_improvement/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /inbox\.counterparty_to_ap/ })).toBeInTheDocument();
});

test("ap.self_improvement is labeled not-built", () => {
  renderCoverage();
  expect(screen.getByRole("button", { name: /ap\.self_improvement/ })).toHaveTextContent(/not-built/i);
});

test("inbox.counterparty_to_ap is labeled partial", () => {
  renderCoverage();
  expect(screen.getByRole("button", { name: /inbox\.counterparty_to_ap/ })).toHaveTextContent(/partial/i);
});

test("Not built filter leaves only not-built cells visible", () => {
  renderCoverage();
  fireEvent.click(screen.getByRole("button", { name: /^Not built$/i }));
  expect(screen.getByRole("button", { name: /ap\.self_improvement/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /ap\.vendor_bank_change/ })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /inbox\.counterparty_to_ap/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /ap\.three_way_match/ })).not.toBeInTheDocument();
});

test("page is a wall of ids, not Finance team / Maximor essays", () => {
  const { container } = renderCoverage();
  expect(container.querySelector(".cap-wall")).not.toBeNull();
  expect(container.querySelector(".coverage-grid")).toBeNull();
  expect(container.textContent).not.toMatch(/Finance team\./);
  expect(container.textContent).not.toMatch(/Maximor\./);
  expect(screen.queryByRole("heading", { name: /Finance functions, not one agent per function/i })).not.toBeInTheDocument();
});

test("gauntlet row captions Kernel, not the office", () => {
  renderCoverage();
  expect(screen.getByRole("button", { name: /evaluation\.finance_gauntlet/ })).toHaveTextContent(
    /Kernel measure, not the office score/,
  );
});

test("clicking cash.bank_reconciliation opens drawer links", () => {
  renderCoverage();
  fireEvent.click(screen.getByRole("button", { name: /cash\.bank_reconciliation/ }));
  expect(screen.getByRole("link", { name: "Cash" })).toHaveAttribute("href", "/cash");
  expect(screen.getByRole("link", { name: "Unresolved story" })).toHaveAttribute(
    "href",
    "/workflow?story=unresolved",
  );
});

test("clicking not-built and partial cells opens a drawer", () => {
  renderCoverage();
  fireEvent.click(screen.getByRole("button", { name: /ap\.self_improvement/ }));
  expect(screen.getByText(/Not built as an office path/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /inbox\.counterparty_to_ap/ }));
  expect(screen.getByText(/World Bot not on live roster/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Inbox" })).toHaveAttribute("href", "/inbox");
});

test("compact mode shows four pipe counts and a link to /coverage", () => {
  render(
    <MemoryRouter>
      <CoverageGrid compact intro />
    </MemoryRouter>,
  );
  expect(screen.getByRole("link", { name: /capability wall/i })).toHaveAttribute("href", "/coverage");
  expect(screen.getByText(/Pay/)).toBeInTheDocument();
  expect(screen.getByText(/2 live \/ 2 not-built/)).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: /What it can do/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: /Finance functions/i })).not.toBeInTheDocument();
});
