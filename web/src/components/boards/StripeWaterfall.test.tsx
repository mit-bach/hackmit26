import { render, screen } from "@testing-library/react";
import { StripeWaterfall } from "./StripeWaterfall";

test("renders waterfall bars and not a waterfall-eq stack", () => {
  const { container } = render(
    <StripeWaterfall
      breakdown={{
        gross_payments: 8000,
        refunds: 500,
        chargebacks: 0,
        fees: 390,
        expected_payout: 7110,
        net: 7110,
      }}
      deposit={7110}
      tied
    />
  );
  expect(container.querySelector(".cash-waterfall")).not.toBeNull();
  expect(container.querySelector(".waterfall-eq")).toBeNull();
  expect(container.querySelectorAll(".cash-waterfall-bar").length).toBeGreaterThan(3);
  expect(screen.getByLabelText("Stripe payout waterfall")).toBeInTheDocument();
  expect(container.textContent).not.toMatch(/\bCLOSED\b/);
});

test("a deposit mismatch is a visible overhang", () => {
  const { container } = render(
    <StripeWaterfall
      breakdown={{
        gross_payments: 1000,
        refunds: 0,
        chargebacks: 0,
        fees: 0,
        expected_payout: 1000,
      }}
      deposit={880}
      tied={false}
    />
  );
  expect(container.querySelector(".cash-waterfall-overhang")).not.toBeNull();
});

test("empty breakdown still renders the six bar rows", () => {
  const { container } = render(<StripeWaterfall />);
  expect(container.querySelector(".cash-waterfall")).not.toBeNull();
  expect(container.querySelectorAll(".cash-waterfall-step").length).toBe(6);
});
