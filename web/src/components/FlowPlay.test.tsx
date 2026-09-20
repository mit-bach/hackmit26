import { fireEvent, render, screen } from "@testing-library/react";
import { FlowPlay } from "./FlowPlay";
import type { FlowEdge, FlowNode, FlowStep } from "./FlowPlay";

const nodes: readonly FlowNode[] = [
  { id: "event", label: "Vendor bill", kind: "event" },
  { id: "ap", label: "AP", kind: "operator" },
];

const edges: readonly FlowEdge[] = [
  { id: "e1", from: "event", to: "ap", label: "bill", attached: false },
];

const steps: readonly FlowStep[] = [
  { id: "s0", title: "Arrives", nodeId: "event", manipulations: ["land"] },
  { id: "s1", title: "Match", nodeId: "ap", manipulations: ["three-way match"] },
];

test("renders node labels from props", () => {
  render(<FlowPlay nodes={nodes} edges={edges} steps={steps} />);
  expect(screen.getByRole("button", { name: "Vendor bill" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "AP" })).toBeInTheDocument();
});

test("clicking Step calls onStepChange with the next id", () => {
  const onStepChange = vi.fn();
  render(<FlowPlay nodes={nodes} edges={edges} steps={steps} onStepChange={onStepChange} />);
  fireEvent.click(screen.getByRole("button", { name: "Step" }));
  expect(onStepChange).toHaveBeenCalledWith("s1");
});

test("an edge with attached false is present in the DOM", () => {
  render(<FlowPlay nodes={nodes} edges={edges} steps={steps} />);
  expect(screen.getByLabelText(/not attached/i)).toBeInTheDocument();
});

test("liveStages marks the matching bot node active", () => {
  render(<FlowPlay nodes={nodes} edges={edges} steps={steps} liveStages={[{ bot: "ap" }]} />);
  const ap = screen.getByRole("button", { name: "AP" });
  expect(ap.className).toMatch(/\bactive\b/);
});
