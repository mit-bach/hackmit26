import { render, screen } from "@testing-library/react";
import Cash from "./Cash";

const fetchMock = vi.fn(async () => {
  return {
    ok: true,
    json: async () => ({ featured_cases: {}, report: { matches: [] } }),
  } as Response;
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("cash is bank vs books with the Northstar gap", async () => {
  const { container } = render(<Cash />);
  expect(await screen.findByRole("heading", { name: /Does the bank agree with the books/i })).toBeInTheDocument();
  expect(screen.getByText("What's happening?")).toBeInTheDocument();
  expect(container.textContent).toMatch(/12\.40|TXN-2026-09-015|\$12,412\.40/);
  expect(container.querySelector(".cash-stage")).not.toBeNull();
  expect(container.textContent).not.toMatch(/\bCLOSED\b/);
});

test("empty matches do not crash cash", async () => {
  render(<Cash />);
  expect(await screen.findByRole("heading", { name: /Does the bank agree with the books/i })).toBeInTheDocument();
});
