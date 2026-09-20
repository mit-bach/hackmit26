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

test("stripe is a bar waterfall with a simulated-mode pill", async () => {
  const { container } = render(<StripePage />);
  expect(await screen.findByRole("heading", { name: "Stripe payout" })).toBeInTheDocument();
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  expect(screen.queryByText("What arrived")).not.toBeInTheDocument();
  expect(container.querySelector(".waterfall-eq")).toBeNull();
  expect(container.querySelector(".cash-waterfall")).not.toBeNull();
  expect(container.querySelectorAll(".cash-waterfall-bar").length).toBeGreaterThan(0);
  expect(screen.getByText(/Stripe Simulated/i)).toBeInTheDocument();
  expect(container.textContent).not.toMatch(/\bCLOSED\b/);
});
