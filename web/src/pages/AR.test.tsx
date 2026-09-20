import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AR from "./AR";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({
      invoices: [],
      payments: [],
      buckets: {},
      outstanding: 0,
    }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderAr(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <AR />
    </MemoryRouter>
  );
}

test("AR render includes aging bucket labels or CURRENT", async () => {
  renderAr();
  await waitFor(() => expect(screen.getAllByText("CURRENT").length).toBeGreaterThan(0));
  expect(screen.getByRole("heading", { name: "Customer cash" })).toBeInTheDocument();
  expect(screen.getByLabelText(/Invoice aging/i)).toBeInTheDocument();
  expect(screen.queryByText(/An invoice that was due 75 days ago/i)).not.toBeInTheDocument();
});

test("AR does not contain email sent or sent the collection as a success string", async () => {
  const { container } = renderAr();
  await waitFor(() => expect(screen.getByRole("heading", { name: "Customer cash" })).toBeInTheDocument());
  const text = container.textContent?.toLowerCase() || "";
  expect(text).not.toMatch(/email sent/);
  expect(text).not.toMatch(/sent the collection/);
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Age unpaid invoices/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Decide collection follow-up/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Match the Lumen Labs payment/i })).toBeInTheDocument();
});
