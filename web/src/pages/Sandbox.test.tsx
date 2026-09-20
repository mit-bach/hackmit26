import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Sandbox from "./Sandbox";

test("sandbox page says the office is not live-connected", () => {
  render(
    <MemoryRouter>
      <Sandbox />
    </MemoryRouter>
  );
  expect(screen.getByRole("heading", { name: /This office is a sandbox/i })).toBeInTheDocument();
  expect(screen.getByText(/not plugged into a live Stripe account/i)).toBeInTheDocument();
  expect(screen.getByText(/not on this demo roster/i)).toBeInTheDocument();
  expect(screen.getByText(/TXN-2026-09-015/)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Live Gmail" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /See how those agents are organized/i })).toHaveAttribute(
    "href",
    "/architecture"
  );
});
