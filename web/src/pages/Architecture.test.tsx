import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import Architecture from "./Architecture";
import { GRAIN_SLUGS } from "../data/agents";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({ bots: [], routines: [] }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("architecture first paint is a graph of Bot buttons and Handle edges", () => {
  const { container } = render(<Architecture />);
  expect(screen.getByRole("heading", { name: "How work moves through the office" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /How the finance team is actually organized/i })).toBeInTheDocument();
  expect(container.querySelector(".arch-rooms")).toBeNull();
  expect(container.querySelector(".arch-node")).toBeNull();
  expect(container.querySelectorAll(".flow-node").length).toBe(GRAIN_SLUGS.length + 1);
  expect(container.querySelectorAll("svg path.flow-edge").length).toBeGreaterThanOrEqual(25);
  expect(container.querySelectorAll("svg path.flow-edge.not-attached").length).toBeGreaterThanOrEqual(1);
  for (const slug of GRAIN_SLUGS) {
    expect(container.querySelector(`[data-node-id="${slug}"]`)).not.toBeNull();
  }
  expect(container.querySelector('[data-node-id="world"]')).not.toBeNull();
  expect(screen.getByRole("heading", { name: "Accounts Payable Agent" })).toBeInTheDocument();
});

test("clicking AP emphasizes its Handles and opens the team panel", () => {
  const { container } = render(<Architecture />);
  fireEvent.click(screen.getByRole("button", { name: "Accounts Payable" }));
  const inspector = container.querySelector(".office-inspector");
  expect(inspector).not.toBeNull();
  expect(inspector?.querySelector(".office-inspector-name")?.textContent).toBe("Accounts Payable Agent");
  expect(inspector?.textContent).toMatch(/Payables Control Agent/);
  expect(inspector?.textContent).toMatch(/Payments Agent/);
  expect(inspector?.textContent).toMatch(/Month-End Close Agent/);
  const apNode = container.querySelector('[data-node-id="ap"]');
  expect(apNode?.className).toMatch(/is-selected/);
});

test("clicking World stays on a static not-attached panel", () => {
  const { container } = render(<Architecture />);
  fireEvent.click(screen.getByRole("button", { name: /World \(not on live roster\)/i }));
  const inspector = container.querySelector(".office-inspector");
  expect(inspector).not.toBeNull();
  expect(inspector?.textContent).toMatch(/not on live roster/i);
  expect(inspector?.textContent).toMatch(/simulated mailbox/i);
  expect(inspector?.textContent).toMatch(/send_office_outbound/i);
  expect(inspector?.querySelector(".office-inspector-name")?.textContent).toBe("World");
});

test("Showcase nav walks Home, How they work, One invoice, and live office", () => {
  render(
    <MemoryRouter initialEntries={["/architecture"]}>
      <App />
    </MemoryRouter>
  );
  const showcase = screen.getByText("Showcase").parentElement;
  expect(showcase).not.toBeNull();
  const showcaseLinks = showcase ? within(showcase).getAllByRole("link").map((link) => link.textContent) : [];
  expect(showcaseLinks).toEqual([
    "Home",
    "How they work",
    "The sandbox",
    "One invoice",
    "Saved decisions",
    "Simulations",
    "Videos",
    "What it covers",
    "Evaluation",
  ]);
  expect(screen.getByRole("link", { name: "One invoice" })).toHaveAttribute("href", "/workflow");
  const live = screen.getByText("Live office", { selector: ".nav-label" }).parentElement;
  expect(live && within(live).getByRole("link", { name: "Cash outlook" })).toBeTruthy();
  expect(live && within(live).queryByRole("link", { name: "The team" })).toBeNull();
  expect(live && within(live).getByRole("link", { name: "Bank vs books" })).toBeTruthy();
});
