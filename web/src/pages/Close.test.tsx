import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Close from "./Close";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({
      status: "BLOCKED",
      tasks: [],
      journals: [],
      harbor: {},
    }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("close desk is a blocked lock, not Harbor essays", async () => {
  const { container } = render(
    <MemoryRouter>
      <Close />
    </MemoryRouter>
  );
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  expect(screen.queryByText("What arrived")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /September is not closed/i })).toBeInTheDocument();
  expect(container.textContent).toMatch(/not closed|BLOCKED|12\.40/);
  expect(screen.queryByText("Invoice approved")).not.toBeInTheDocument();
  expect(container.querySelector("svg.month-gate-edges")).not.toBeNull();
  expect(container.innerHTML).not.toContain("DemoLayout");
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
});
