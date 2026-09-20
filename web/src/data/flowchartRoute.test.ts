import { GRAIN_SLUGS } from "./agents";
import { OFFICE_GRAPH_EDGES, OFFICE_GRAPH_NODES, isPrincipalHandle } from "./officeGraph";
import {
  labelsOverlap,
  layoutOfficeNodes,
  nudgeLabels,
  routeOfficeEdges,
  type LabelAnchor,
} from "./flowchartRoute";

test("office layout places every grain and World in non-overlapping boxes", () => {
  const layout = layoutOfficeNodes(OFFICE_GRAPH_NODES);
  expect(layout.boxes.size).toBe(GRAIN_SLUGS.length + 1);
  const boxes = [...layout.boxes.values()];
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i];
      const b = boxes[j];
      const overlap =
        a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
      expect(overlap).toBe(false);
    }
  }
});

test("same-row adjacent Handles stay a straight run; skip-column Handles elbow", () => {
  const layout = layoutOfficeNodes();
  const routed = routeOfficeEdges(OFFICE_GRAPH_EDGES, layout);
  const bill = routed.find((edge) => edge.id === "email-bill-ap");
  const remittance = routed.find((edge) => edge.id === "email-remittance-apply");
  expect(bill?.d).toMatch(/^M [\d.]+ [\d.]+ H [\d.]+$/);
  expect(remittance?.d).toContain(" V ");
});

test("nudged principal Handle labels do not sit on top of each other", () => {
  const layout = layoutOfficeNodes();
  const routed = routeOfficeEdges(OFFICE_GRAPH_EDGES, layout);
  const anchors: LabelAnchor[] = routed.flatMap((route) => {
    const edge = OFFICE_GRAPH_EDGES.find((item) => item.id === route.id);
    if (!edge || !(isPrincipalHandle(edge) || edge.attached === false)) {
      return [];
    }
    return [
      {
        id: route.id,
        text: edge.when,
        x: route.labelX,
        y: route.labelY,
      },
    ];
  });
  const placed = nudgeLabels(anchors, [...layout.boxes.values()]);
  const overlaps = placed.flatMap((left, i) =>
    placed.slice(i + 1).flatMap((right) => (labelsOverlap(left, right) ? [`${left.id}@${left.x},${left.y} vs ${right.id}@${right.x},${right.y}`] : []))
  );
  expect(overlaps).toEqual([]);
});
