import { render, screen } from "@testing-library/react";
import { leftoverTasks, PLANTED_GAP, PLANTED_TXN } from "./CloseGate";
import { CloseGate } from "./CloseGate";
import type { CloseTask } from "./CloseGate";

test("lock is blocked with planted unexplained cash", () => {
  const { container } = render(<CloseGate />);
  expect(container.textContent).toMatch(/not closed/i);
  expect(container.textContent).toContain(PLANTED_GAP);
  expect(container.textContent).toContain(PLANTED_TXN);
  const lock = screen.getByRole("button", { name: /ctl-books/i });
  expect(lock.className).toMatch(/\bblocked\b/);
  expect(lock.className).toMatch(/\block\b/);
  expect(lock.textContent).toMatch(/BLOCKED/);
});

test("gate nodes are keyboard buttons", () => {
  render(<CloseGate />);
  const nodes = screen.getAllByRole("button");
  expect(nodes.length).toBeGreaterThanOrEqual(6);
});

test("task labels use formatTask when ids match", () => {
  const tasks: CloseTask[] = [
    { task_id: "TASK-ACCRUAL", status: "COMPLETE" },
    { task_id: "TASK-CASH", status: "BLOCKED" },
  ];
  render(<CloseGate tasks={tasks} status="BLOCKED" />);
  expect(screen.getByRole("button", { name: /Accrued expenses/i })).toBeInTheDocument();
  expect(leftoverTasks(tasks).map((task) => task.task_id)).toEqual(["TASK-CASH"]);
});

test("does not stamp the month closed", () => {
  const { container } = render(<CloseGate status="BLOCKED" />);
  expect(container.textContent).not.toMatch(/\bClosed\b/);
  expect(container.querySelector(".month-gate-node.lock.ok")).toBeNull();
});
