import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App, { ROUTES } from "./App";

const fetchMock = vi.fn(async () => {
  const empty = {
    invoices: [],
    samples: [],
    emails: [],
    bots: [],
    scenarios: [],
    briefing: [],
    operations: [],
    recent_decisions: [],
    activity: [],
    metrics: {},
    company: { company: { legal_name: "Maximor Demo Corp" } },
    buckets: {},
    payouts: [],
    tasks: [],
    weeks: [],
    events: [],
    catalog: [],
    controls: [],
    population: {},
  };
  return {
    ok: true,
    json: async () => empty,
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("route table includes the operations shell", () => {
  expect(ROUTES).toEqual(
    expect.arrayContaining(["/", "/inbox", "/ap", "/ar", "/cash", "/stripe", "/close", "/forecast", "/audit", "/memory", "/agents", "/evaluations", "/scenarios", "/architecture", "/simulations", "/videos", "/workflow", "/coverage"])
  );
});

test.each(ROUTES)("renders %s without hardcoded demo success copy", async (route) => {
  render(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>
  );
  expect(screen.getAllByText(/Office of the CFO/).length).toBeGreaterThan(0);
  expect(screen.queryByText("Invoice approved")).not.toBeInTheDocument();
});

test("inbox classify stage has curated documents and a run control", async () => {
  const { container } = render(
    <MemoryRouter initialEntries={["/inbox"]}>
      <App />
    </MemoryRouter>
  );
  expect(screen.queryByText("Invoice approved")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /What just arrived in finance email/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Identify this document/i })).toBeInTheDocument();
  expect(screen.getAllByText(/August warehouse supplies invoice/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Quote for office renovation/i).length).toBeGreaterThan(0);
  expect(container.querySelector(".io-flow")).not.toBeNull();
});

test("audit and memory omit the happening essay", async () => {
  const audit = render(
    <MemoryRouter initialEntries={["/audit"]}>
      <App />
    </MemoryRouter>
  );
  expect(screen.getByRole("heading", { name: /Independent tests/i })).toBeInTheDocument();
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  audit.unmount();

  render(
    <MemoryRouter initialEntries={["/memory"]}>
      <App />
    </MemoryRouter>
  );
  expect(screen.getByRole("heading", { name: /August still matters/i })).toBeInTheDocument();
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
});

test("agents page is the team directory with recent activity", async () => {
  render(
    <MemoryRouter initialEntries={["/agents"]}>
      <App />
    </MemoryRouter>
  );
  expect(await screen.findByRole("heading", { name: /The finance team/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "The team" })).toBeInTheDocument();
  expect(screen.getByText(/Who it works with/i)).toBeInTheDocument();
  expect(screen.queryByText("Fifteen bots")).not.toBeInTheDocument();
  expect(screen.queryByText(/43 autonomous agents/i)).not.toBeInTheDocument();
});

test("evaluations route is the kernel gauntlet scoreboard", async () => {
  render(
    <MemoryRouter initialEntries={["/evaluations"]}>
      <App />
    </MemoryRouter>
  );
  expect(await screen.findByRole("heading", { name: /Kernel gauntlet/i })).toBeInTheDocument();
  expect(screen.queryByText(/connected finance work/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Evaluation Lab/i)).not.toBeInTheDocument();
  const text = document.body.textContent || "";
  if (/42|97/.test(text)) {
    expect(text).toMatch(/Kernel/);
  }
});
