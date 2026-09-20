import { render, screen } from "@testing-library/react";
import StripePage from "./StripePage";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({ payouts: [], mode: { mode: "simulated" } }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("stripe explains how a payout became a bank deposit", async () => {
  const { container } = render(<StripePage />);
  expect(await screen.findByRole("heading", { name: /How a Stripe payout became a bank deposit/i })).toBeInTheDocument();
  expect(screen.getByText("What's happening?")).toBeInTheDocument();
  expect(container.querySelector(".cash-waterfall")).not.toBeNull();
  expect(screen.getByText(/Stripe simulated/i)).toBeInTheDocument();
  expect(container.textContent).not.toMatch(/\bCLOSED\b/);
});
