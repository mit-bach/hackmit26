import { fireEvent, render, screen } from "@testing-library/react";
import { ForecastLine, type ForecastWeek } from "./ForecastLine";

function makeWeeks(count: number): ForecastWeek[] {
  return Array.from({ length: count }, (_, index) => {
    const start = new Date(Date.UTC(2026, 8, 14 + index * 7));
    const end = new Date(Date.UTC(2026, 8, 20 + index * 7));
    const iso = (date: Date): string => date.toISOString().slice(0, 10);
    return {
      week_start: iso(start),
      week_end: iso(end),
      beginning_cash: 200000 - index * 8000,
      ending_cash: 192000 - index * 8000,
      ar_collections: 12000,
      ap_payments: 20000,
      line_ids: index === 2 ? ["FL-AR-INV-AR-014"] : [],
    };
  });
}

test("empty weeks still render the stage and Run forecast", () => {
  render(<ForecastLine weeks={[]} />);
  expect(screen.getByTestId("forecast-line")).toBeInTheDocument();
  expect(screen.getByText("Run forecast")).toBeInTheDocument();
  expect(screen.getByTestId("forecast-line").querySelectorAll("circle").length).toBe(0);
});

test("draws 13 polyline points when weeks has 13", () => {
  render(<ForecastLine weeks={makeWeeks(13)} />);
  const svg = screen.getByTestId("forecast-line");
  expect(svg.querySelector("polyline")).not.toBeNull();
  expect(svg.querySelectorAll("circle").length).toBe(13);
});

test("clicking a point selects that week", () => {
  const onSelectWeek = vi.fn();
  const weeks = makeWeeks(13);
  render(<ForecastLine weeks={weeks} onSelectWeek={onSelectWeek} />);
  fireEvent.click(screen.getAllByRole("button")[2]);
  expect(onSelectWeek).toHaveBeenCalledWith(weeks[2]);
});

test("marks INV-AR-014 only when missId is provided", () => {
  const weeks = makeWeeks(13);
  const { rerender } = render(<ForecastLine weeks={weeks} />);
  expect(screen.queryByText("INV-AR-014")).not.toBeInTheDocument();
  rerender(<ForecastLine weeks={weeks} missId="INV-AR-014" />);
  expect(screen.getByText("INV-AR-014")).toBeInTheDocument();
});
