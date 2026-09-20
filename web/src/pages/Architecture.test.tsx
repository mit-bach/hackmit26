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
  expect(screen.getByRole("heading", { name: "The office" })).toBeInTheDocument();
  expect(container.querySelector(".arch-rooms")).toBeNull();
  expect(container.querySelector(".arch-node")).toBeNull();
  expect(container.querySelectorAll(".flow-node").length).toBe(GRAIN_SLUGS.length + 1);
  expect(container.querySelectorAll("svg path.flow-edge").length).toBeGreaterThanOrEqual(25);
  expect(container.querySelectorAll("svg path.flow-edge.not-attached").length).toBeGreaterThanOrEqual(1);
  for (const slug of GRAIN_SLUGS) {
    expect(container.querySelector(`[data-node-id="${slug}"]`)).not.toBeNull();
  }
  expect(container.querySelector('[data-node-id="world"]')).not.toBeNull();
  expect(screen.queryByRole("heading", { name: "Accounts Payable Agent" })).not.toBeInTheDocument();
});

test("clicking AP emphasizes its Handles and opens an inspector", () => {
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
  expect(container.querySelector("details")).toBeNull();
});

test("Pitch nav walks Home, Office graph, Three stories, Capabilities, Evidence", () => {
  render(
    <MemoryRouter initialEntries={["/architecture"]}>
      <App />
    </MemoryRouter>
  );
  const pitch = screen.getByText("Pitch").parentElement;
  expect(pitch).not.toBeNull();
  const pitchLinks = pitch ? within(pitch).getAllByRole("link").map((link) => link.textContent) : [];
  expect(pitchLinks).toEqual(["Home", "Office graph", "Three stories", "Capabilities", "Evidence"]);
  expect(screen.getByText("Capabilities")).toBeInTheDocument();
  expect(screen.queryByText("Showcase")).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "One invoice" })).not.toBeInTheDocument();
  const live = screen.getByText("Live office").parentElement;
  expect(live && within(live).getByRole("link", { name: "Memory" })).toBeTruthy();
  const more = screen.getByText("More").parentElement;
  expect(more && within(more).getByRole("link", { name: "Simulations" })).toBeTruthy();
  expect(more && within(more).getByRole("link", { name: "Videos" })).toBeTruthy();
});
