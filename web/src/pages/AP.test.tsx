import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AP from "./AP";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({ invoices: [] }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderAp(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <AP />
    </MemoryRouter>
  );
}

test("AP does not render What's happening? or What arrived", async () => {
  const { container } = renderAp();
  await waitFor(() => expect(screen.getByRole("heading", { name: "Vendor bills" })).toBeInTheDocument());
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  expect(screen.queryByText("What arrived")).not.toBeInTheDocument();
  expect(container.querySelector(".io-flow")).toBeNull();
  expect(container.textContent).not.toMatch(/DemoLayout/);
});

test("AP render can show INV-003 by default and includes a way to see INV-001", async () => {
  renderAp();
  await waitFor(() => expect(screen.getByRole("button", { name: /INV-003/ })).toHaveAttribute("aria-pressed", "true"));
  expect(screen.getByRole("button", { name: /Clean/i })).toHaveTextContent("INV-001");
  expect(screen.getByRole("heading", { name: "Vendor bills" })).toBeInTheDocument();
  expect(screen.getByText("Invoice")).toBeInTheDocument();
  expect(screen.getByText("Purchase order")).toBeInTheDocument();
  expect(screen.getByText("Goods receipt")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Check this vendor bill/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Draft this week's payments/i })).toBeInTheDocument();
});
