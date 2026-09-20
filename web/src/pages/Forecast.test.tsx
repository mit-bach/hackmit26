import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Forecast from "./Forecast";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({
      weeks: [
        {
          week_start: "2026-09-21",
          week_end: "2026-09-27",
          beginning_cash: 510000,
          ar_collections: 20000,
          ap_payments: 10000,
          ending_cash: 520000,
        },
      ],
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

test("forecast shows weekly cash outlook and the 13-week line", async () => {
  const { container } = render(
    <MemoryRouter>
      <Forecast />
    </MemoryRouter>
  );
  expect(screen.getByRole("heading", { name: /How much cash will be in the bank/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /Weekly cash outlook/i })).toBeInTheDocument();
  expect(screen.getByText("Week ending")).toBeInTheDocument();
  expect(screen.getByTestId("forecast-line")).toBeInTheDocument();
  expect(container.querySelector("svg")).not.toBeNull();
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
});
