import { GRAIN_SLUGS } from "./agents";
import { HANDOFFS } from "./handoffs";
import {
  OFFICE_GRAPH_EDGES,
  OFFICE_GRAPH_NODES,
  WORLD_NODE_ID,
  edgeWeight,
  isPrincipalHandle,
} from "./officeGraph";

test("office graph keeps all 15 grain ids and adds World", () => {
  const ids = OFFICE_GRAPH_NODES.map((node) => node.id);
  for (const slug of GRAIN_SLUGS) {
    expect(ids).toContain(slug);
  }
  expect(ids).toContain(WORLD_NODE_ID);
  expect(GRAIN_SLUGS as readonly string[]).not.toContain(WORLD_NODE_ID);
  expect(OFFICE_GRAPH_NODES.filter((node) => node.id === WORLD_NODE_ID)).toHaveLength(1);
});

test("office graph includes every live Handle and at least one detached World edge", () => {
  for (const handoff of HANDOFFS) {
    expect(
      OFFICE_GRAPH_EDGES.some(
        (edge) => edge.from === handoff.from && edge.to === handoff.to && edge.when === handoff.when
      )
    ).toBe(true);
  }
  expect(OFFICE_GRAPH_EDGES.some((edge) => edge.attached === false)).toBe(true);
  expect(OFFICE_GRAPH_EDGES.filter((edge) => edge.attached === false).length).toBeGreaterThanOrEqual(1);
});

test("principal Handles stay opaque until a Bot is selected", () => {
  const vendorBill = OFFICE_GRAPH_EDGES.find((edge) => edge.from === "email" && edge.to === "ap");
  const sameRoom = OFFICE_GRAPH_EDGES.find((edge) => edge.from === "ap" && edge.to === "pay");
  expect(vendorBill).toBeTruthy();
  expect(sameRoom).toBeTruthy();
  if (!vendorBill || !sameRoom) {
    return;
  }
  expect(isPrincipalHandle(vendorBill)).toBe(true);
  expect(edgeWeight(vendorBill, null, false)).toBe(1);
  expect(edgeWeight(sameRoom, null, false)).toBe(0.22);
  expect(edgeWeight(sameRoom, "ap", false)).toBe(1);
  expect(edgeWeight(vendorBill, "cash", false)).toBe(0.12);
});
