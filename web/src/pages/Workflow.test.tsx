import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Workflow from "./Workflow";

function renderWorkflow(path = "/workflow"): ReturnType<typeof render> {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Workflow />
    </MemoryRouter>
  );
}

test("first paint is the one-invoice path plus the three case files", () => {
  const { container } = renderWorkflow();
  expect(screen.getByRole("heading", { name: /Follow a vendor invoice through the office/i })).toBeInTheDocument();
  expect(container.querySelector("ol.story-timeline")).not.toBeNull();
  expect(screen.getByRole("heading", { name: /Three invoices, one set of books/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /^CLEAN/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /^RESOLVED/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /^UNRESOLVED/i })).toBeInTheDocument();
});

test("CLEAN ticker includes INV-001 and TXN-2026-09-018A", () => {
  renderWorkflow();
  const ticker = screen.getByLabelText("Case identities");
  expect(ticker).toHaveTextContent("INV-001");
  expect(ticker).toHaveTextContent("PO-101");
  expect(ticker).toHaveTextContent("GR-101");
  expect(ticker).toHaveTextContent("PAY-AP-001");
  expect(ticker).toHaveTextContent("TXN-2026-09-018A");
});

test("switching to Unresolved shows the $12.40 gap and not CLOSED", () => {
  const { container } = renderWorkflow();
  fireEvent.click(screen.getByRole("button", { name: /^UNRESOLVED/i }));
  const ticker = screen.getByLabelText("Case identities");
  expect(ticker).toHaveTextContent("TXN-2026-09-015");
  expect(ticker).not.toHaveTextContent("INV-001");
  expect(container.textContent).toMatch(/12\.40|\$12,412\.40/);
  expect(container.textContent).not.toMatch(/\bCLOSED\b/);
  expect(screen.getByRole("link", { name: /Month cannot finish/i })).toHaveAttribute("href", "/close");
});

test("Resolved names FEE-729103 and FEE_NETTED", () => {
  renderWorkflow();
  fireEvent.click(screen.getByRole("button", { name: /^RESOLVED/i }));
  expect(screen.getByLabelText("Case identities")).toHaveTextContent("FEE-729103");
  expect(screen.getByRole("button", { name: /^RESOLVED/i })).toHaveTextContent("FEE_NETTED");
});

test("/workflow?story=unresolved selects the Unresolved case", () => {
  renderWorkflow("/workflow?story=unresolved");
  expect(screen.getByRole("button", { name: /^UNRESOLVED/i })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByLabelText("Case identities")).toHaveTextContent("TXN-2026-09-015");
  expect(screen.getByRole("link", { name: /Month cannot finish/i })).toBeInTheDocument();
});
