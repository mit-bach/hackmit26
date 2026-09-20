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

test("AP explains vendor bills waiting to be paid", async () => {
  renderAp();
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /Vendor bills waiting to be paid/i })).toBeInTheDocument()
  );
  expect(screen.getByText("What's happening?")).toBeInTheDocument();
  expect(screen.getByText("What arrived")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Check this vendor bill/i })).toBeInTheDocument();
});
