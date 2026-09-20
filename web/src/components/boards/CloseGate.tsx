import { useMemo, useState } from "react";
import { formatStatus, formatTask } from "../../copy";

export const PLANTED_TXN = "TXN-2026-09-015";
export const PLANTED_GAP = "$12.40";

export interface CloseTask {
  readonly task_id?: string;
  readonly status?: string;
  readonly category?: string;
  readonly blocker_reason?: string;
  readonly blocking_items?: readonly string[];
  readonly evidence_refs?: readonly string[];
}

export interface CloseGateProps {
  readonly tasks?: readonly CloseTask[];
  readonly status?: string;
  readonly selectedId?: string;
  readonly onSelect?: (id: string) => void;
}

interface GateDef {
  readonly id: string;
  readonly taskIds: readonly string[];
  readonly x: number;
  readonly y: number;
  readonly lock?: boolean;
}

interface NodeBox {
  readonly id: string;
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
}

type NodeTone = "idle" | "ok" | "warn" | "blocked";

const CANVAS_W = 960;
const CANVAS_H = 400;
const NODE_W = 156;
const NODE_H = 54;
const LOCK_W = 180;
const LOCK_H = 108;

const GATE_NODES: readonly GateDef[] = [
  { id: "accrue", taskIds: ["TASK-ACCRUAL", "accruals"], x: 36, y: 40 },
  { id: "prepaid", taskIds: ["TASK-PREPAID", "prepaid"], x: 36, y: 154 },
  { id: "assets", taskIds: ["TASK-FA", "depreciation"], x: 36, y: 268 },
  { id: "bs", taskIds: ["TASK-BS", "bs"], x: 268, y: 154 },
  { id: "coordinate", taskIds: ["TASK-FINAL", "final"], x: 500, y: 154 },
  { id: "lock", taskIds: ["ctl-books"], x: 744, y: 118, lock: true },
];

const GATE_TASK_IDS = new Set(
  GATE_NODES.flatMap((node) => node.taskIds).filter((id) => id.startsWith("TASK-"))
);

export function leftoverTasks(tasks: readonly CloseTask[]): CloseTask[] {
  return tasks.filter((task) => {
    const id = String(task.task_id || "");
    return id !== "" && !GATE_TASK_IDS.has(id);
  });
}

function cx(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function taskMatches(task: CloseTask, def: GateDef): boolean {
  const id = String(task.task_id || "");
  const category = String(task.category || "");
  return def.taskIds.includes(id) || def.taskIds.includes(category);
}

function toneFromStatus(status: string | undefined): NodeTone {
  const value = (status || "").toLowerCase();
  if (value.includes("block") || value.includes("unreconcil") || value.includes("fail")) {
    return "blocked";
  }
  if (value.includes("review") || value.includes("hold") || value.includes("open")) {
    return "warn";
  }
  if (value.includes("complete") || value.includes("closed") || value.includes("tied")) {
    return "ok";
  }
  return "idle";
}


function boxFor(def: GateDef): NodeBox {
  return {
    id: def.id,
    x: def.x,
    y: def.y,
    w: def.lock ? LOCK_W : NODE_W,
    h: def.lock ? LOCK_H : NODE_H,
  };
}

function port(box: NodeBox, side: "left" | "right" | "bottom" | "top"): { readonly x: number; readonly y: number } {
  if (side === "left") {
    return { x: box.x, y: box.y + box.h / 2 };
  }
  if (side === "right") {
    return { x: box.x + box.w, y: box.y + box.h / 2 };
  }
  if (side === "top") {
    return { x: box.x + box.w / 2, y: box.y };
  }
  return { x: box.x + box.w / 2, y: box.y + box.h };
}

function edgePath(
  from: { readonly x: number; readonly y: number },
  to: { readonly x: number; readonly y: number }
): string {
  const mid = (from.x + to.x) / 2;
  return `M ${from.x} ${from.y} C ${mid} ${from.y}, ${mid} ${to.y}, ${to.x} ${to.y}`;
}

function nodeLabel(def: GateDef, task: CloseTask | undefined): string {
  if (def.lock) {
    return "ctl-books";
  }
  if (task?.task_id) {
    return formatTask(task.task_id);
  }
  return formatTask(def.taskIds[0]);
}

export function CloseGate(props: CloseGateProps): JSX.Element {
  const { tasks = [], status, selectedId, onSelect } = props;
  const [internalId, setInternalId] = useState<string>("lock");
  const activeId = selectedId ?? internalId;

  const byNode = useMemo(() => {
    const map = new Map<string, CloseTask>();
    for (const def of GATE_NODES) {
      const match = tasks.find((task) => taskMatches(task, def));
      if (match) {
        map.set(def.id, match);
      }
    }
    return map;
  }, [tasks]);

  const boxes = useMemo(() => new Map(GATE_NODES.map((def) => [def.id, boxFor(def)])), []);
  const accrue = boxes.get("accrue");
  const prepaid = boxes.get("prepaid");
  const assets = boxes.get("assets");
  const bs = boxes.get("bs");
  const coordinate = boxes.get("coordinate");
  const lock = boxes.get("lock");
  const activeTask = byNode.get(activeId);
  const activeDef = GATE_NODES.find((def) => def.id === activeId);

  function select(id: string): void {
    setInternalId(id);
    onSelect?.(id);
  }

  return (
    <div className="month-gate" data-testid="close-gate">
      <div className="month-gate-canvas">
        <div className="month-gate-inner" style={{ width: CANVAS_W, height: CANVAS_H }}>
          <svg
            className="month-gate-edges"
            width={CANVAS_W}
            height={CANVAS_H}
            viewBox={`0 0 ${CANVAS_W} ${CANVAS_H}`}
            aria-hidden="false"
          >
            {accrue && bs ? (
              <path className="month-gate-edge" d={edgePath(port(accrue, "right"), port(bs, "left"))} />
            ) : null}
            {prepaid && bs ? (
              <path className="month-gate-edge" d={edgePath(port(prepaid, "right"), port(bs, "left"))} />
            ) : null}
            {assets && bs ? (
              <path className="month-gate-edge" d={edgePath(port(assets, "right"), port(bs, "left"))} />
            ) : null}
            {bs && coordinate ? (
              <path className="month-gate-edge" d={edgePath(port(bs, "right"), port(coordinate, "left"))} />
            ) : null}
            {coordinate && lock ? (
              <path className="month-gate-edge" d={edgePath(port(coordinate, "right"), port(lock, "left"))} />
            ) : null}
            {lock ? (
              <path
                className="month-gate-edge blocked"
                d={edgePath({ x: 268, y: 360 }, port(lock, "bottom"))}
              />
            ) : null}
            <text className="month-gate-edge-label blocked" x={430} y={352}>
              {PLANTED_TXN} · {PLANTED_GAP}
            </text>
          </svg>
          {GATE_NODES.map((def) => {
            const box = boxes.get(def.id);
            if (!box) {
              return null;
            }
            const task = byNode.get(def.id);
            const tone: NodeTone = def.lock ? "blocked" : toneFromStatus(task?.status);
            const label = nodeLabel(def, task);
            const lockish = Boolean(def.lock);
            return (
              <button
                key={def.id}
                type="button"
                className={cx(
                  "month-gate-node",
                  lockish && "lock",
                  tone,
                  activeId === def.id && "active"
                )}
                style={{ left: box.x, top: box.y, width: box.w, height: box.h }}
                aria-pressed={activeId === def.id}
                aria-label={lockish ? `${label} blocked` : label}
                data-node-id={def.id}
                onClick={() => select(def.id)}
              >
                <span className="month-gate-node-label">{label}</span>
                {lockish ? <span className="month-gate-lock-status">BLOCKED</span> : null}
              </button>
            );
          })}
        </div>
      </div>
      <p className="month-gate-caption">
        Month is not closed. Unexplained cash {PLANTED_GAP} on <span className="mono">{PLANTED_TXN}</span> keeps
        ctl-books from seating the lock.
        {status ? (
          <>
            {" "}
            Kernel <span className="mono">{status}</span>.
          </>
        ) : null}
      </p>
      {activeDef && !activeDef.lock && activeTask ? (
        <p className="month-gate-note">
          {nodeLabel(activeDef, activeTask)} · {formatStatus(activeTask.status)}
          {activeTask.blocker_reason ? ` — ${activeTask.blocker_reason}` : ""}
        </p>
      ) : null}
    </div>
  );
}
