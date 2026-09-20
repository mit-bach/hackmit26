import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Forecast from "./Forecast";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({
      weeks: [],
      miss: {},
    }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("forecast desk renders a line chart, not the weekly table first", async () => {
  const { container } = render(
    <MemoryRouter>
      <Forecast />
    </MemoryRouter>
  );
  expect(screen.getByRole("heading", { name: /13-week cash/i })).toBeInTheDocument();
  expect(screen.getByTestId("forecast-line")).toBeInTheDocument();
  expect(container.querySelector("svg")).not.toBeNull();
  expect(screen.queryByText("What's happening?")).not.toBeInTheDocument();
  expect(screen.queryByText("Week ending")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Numbers" })).toBeInTheDocument();
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
});
