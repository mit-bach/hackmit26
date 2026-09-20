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

test("AR explains money customers still owe", async () => {
  renderAr();
  await waitFor(() => expect(screen.getByRole("heading", { name: /Money customers still owe/i })).toBeInTheDocument());
  expect(screen.getAllByText(/Lumen Labs/i).length).toBeGreaterThan(0);
  expect(screen.getByRole("button", { name: /Age unpaid invoices/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Match the Lumen Labs payment/i })).toBeInTheDocument();
});

test("AR does not contain email sent as a success string", async () => {
  const { container } = renderAr();
  await waitFor(() => expect(screen.getByRole("heading", { name: /Money customers still owe/i })).toBeInTheDocument());
  const text = container.textContent?.toLowerCase() || "";
  expect(text).not.toMatch(/email sent/);
  expect(text).not.toMatch(/sent the collection/);
});
