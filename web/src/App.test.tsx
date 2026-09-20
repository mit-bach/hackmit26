import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App, { ROUTES } from "./App";

const fetchMock = vi.fn(async (input: RequestInfo) => {
  const url = String(input);
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
    expect.arrayContaining(["/", "/inbox", "/ap", "/ar", "/cash", "/stripe", "/close", "/forecast", "/audit", "/memory", "/agents", "/evaluations", "/scenarios", "/architecture"])
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

test("demo layout exposes original input and final output", async () => {
  render(
    <MemoryRouter initialEntries={["/inbox"]}>
      <App />
    </MemoryRouter>
  );
  expect(screen.getAllByText(/Original input/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Final output/i).length).toBeGreaterThan(0);
});

test("agents page uses specialized finance agents framing", async () => {
  render(
    <MemoryRouter initialEntries={["/agents"]}>
      <App />
    </MemoryRouter>
  );
  expect(await screen.findByText(/15 specialized finance agents/i)).toBeInTheDocument();
  expect(screen.queryByText("Fifteen bots")).not.toBeInTheDocument();
});

test("evaluations route is the evaluation lab", async () => {
  render(
    <MemoryRouter initialEntries={["/evaluations"]}>
      <App />
    </MemoryRouter>
  );
  expect(await screen.findByText(/connected finance work/i)).toBeInTheDocument();
  expect(screen.getAllByText(/Evaluation Lab/i).length).toBeGreaterThan(0);
});
