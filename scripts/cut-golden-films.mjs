#!/usr/bin/env node
/**
 * Cut 1920×1080 H.264 films from golden-20260920-r1.
 * SVG frames → qlmanage PNG → ffmpeg. No Chrome.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, existsSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const GOLDEN = join(ROOT, ".cfo-v2/office/instances/golden-20260920-r1");
const PROTOCOL = join(GOLDEN, "harness/protocol.jsonl");
const SCENES = join(GOLDEN, "harness/demo/latest/scenes.json");
const ROSTER = join(GOLDEN, "harness/roster.json");
const OUT = join(ROOT, "web/public/videos");
const W = 1920;
const H = 1080;

const CUTS = [
  {
    id: "invoice-to-close",
    scene: "C",
    title: "INV-001 reaches control",
    subtitle: "AP prepares. ctl-pay concurs. AP does not pay.",
  },
  {
    id: "stripe-reconciliation",
    scene: "stripe",
    title: "Stripe payout unpack",
    subtitle: "Charges, refunds, and fees on the tape. Not a closed bank match.",
  },
  {
    id: "month-end-across-periods",
    scene: "M",
    title: "Harbor Electric, two periods",
    subtitle: "August $7,800 method recalled. September $4,650. Lock still BLOCKED.",
  },
  {
    id: "agent-memory",
    scene: "M",
    title: "September reads August",
    subtitle: "memory_read / memory_write. Same method. Not last month's number.",
  },
  {
    id: "bad-invoice",
    scene: "B",
    title: "Inbox traps stay off the books",
    subtitle: "Quote, statement, and newsletter never become payables.",
  },
  {
    id: "control-escalation",
    scene: "E",
    title: "$12.40 stays unexplained",
    subtitle: "Cash HUMAN_REVIEW. ctl-cash. The month does not close.",
  },
];

const COLORS = ["#2dd4bf", "#60a5fa", "#c084fc", "#f472b6", "#fb923c", "#22d3ee"];

function ensure(dir) {
  mkdirSync(dir, { recursive: true });
}

function readJsonl(path) {
  return readFileSync(path, "utf8")
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line));
}

function xml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function wrap(text, width) {
  const words = String(text ?? "").replace(/\s+/g, " ").trim().split(" ");
  const lines = [];
  let row = "";
  for (const word of words) {
    const next = row ? `${row} ${word}` : word;
    if (next.length > width && row) {
      lines.push(row);
      row = word;
    } else {
      row = next;
    }
  }
  if (row) lines.push(row);
  return lines.slice(0, 8);
}

function layout(count) {
  if (count <= 1) return [{ x: 48, y: 48, w: W - 96, h: 760 }];
  if (count === 2) {
    return [
      { x: 48, y: 48, w: 900, h: 760 },
      { x: 972, y: 48, w: 900, h: 760 },
    ];
  }
  if (count === 3) {
    return [
      { x: 48, y: 48, w: 900, h: 760 },
      { x: 972, y: 48, w: 900, h: 368 },
      { x: 972, y: 440, w: 900, h: 368 },
    ];
  }
  return [
    { x: 48, y: 48, w: 900, h: 368 },
    { x: 972, y: 48, w: 900, h: 368 },
    { x: 48, y: 440, w: 900, h: 368 },
    { x: 972, y: 440, w: 900, h: 368 },
  ];
}

function titleSvg(title, subtitle) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#07090c"/>
  <circle cx="360" cy="220" r="420" fill="#1a2430"/>
  <text x="72" y="820" fill="#c9a24a" font-size="22" font-family="Helvetica" letter-spacing="6">MAXIMOR · GOLDEN DESK</text>
  <text x="72" y="900" fill="#e8edf2" font-size="64" font-family="Helvetica">${xml(title)}</text>
  <text x="72" y="960" fill="#b7c0ca" font-size="28" font-family="Helvetica">${xml(subtitle)}</text>
</svg>`;
}

function frameSvg({ title, kicker, caption, panes }) {
  const cells = layout(Math.max(1, panes.length));
  const paneMarkup = panes
    .map((pane, index) => {
      const cell = cells[index] ?? cells[0];
      const color = COLORS[index % COLORS.length];
      const lines = wrap(pane.text, panes.length >= 3 ? 42 : 48);
      const text = lines
        .map((line, lineIndex) => `<tspan x="${cell.x + 28}" dy="${lineIndex === 0 ? 0 : 32}">${xml(line)}</tspan>`)
        .join("");
      return `
      <g>
        <rect x="${cell.x}" y="${cell.y}" width="${cell.w}" height="${cell.h}" rx="18" fill="#10141a" stroke="rgba(255,255,255,0.08)"/>
        <circle cx="${cell.x + 28}" cy="${cell.y + 32}" r="7" fill="${color}"/>
        <text x="${cell.x + 48}" y="${cell.y + 40}" fill="#e8edf2" font-size="26" font-family="Helvetica">${xml(pane.name)}</text>
        <rect x="${cell.x + cell.w - 220}" y="${cell.y + 16}" width="200" height="32" rx="16" fill="rgba(45,212,191,0.16)"/>
        <text x="${cell.x + cell.w - 120}" y="${cell.y + 38}" text-anchor="middle" fill="#5eead4" font-size="16" font-family="Helvetica">${xml(pane.activity)}</text>
        <text x="${cell.x + 28}" y="${cell.y + 96}" fill="#d5dde6" font-size="22" font-family="Helvetica">${text}</text>
      </g>`;
    })
    .join("");
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#07090c"/>
  ${paneMarkup}
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#07090c" stop-opacity="0"/>
      <stop offset="0.45" stop-color="#07090c" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#07090c" stop-opacity="0.94"/>
    </linearGradient>
  </defs>
  <rect x="0" y="760" width="${W}" height="320" fill="url(#fade)"/>
  <text x="72" y="900" fill="#c9a24a" font-size="18" font-family="Helvetica" letter-spacing="4">${xml(kicker)}</text>
  <text x="72" y="952" fill="#e8edf2" font-size="40" font-family="Helvetica">${xml(title)}</text>
  <text x="72" y="1004" fill="#b7c0ca" font-size="22" font-family="Helvetica">${xml(caption)}</text>
</svg>`;
}

function run(cmd, args) {
  const result = spawnSync(cmd, args, { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`${cmd} ${args[0] ?? ""} failed: ${(result.stderr || result.stdout || "").slice(-600)}`);
  }
  return result;
}

function raster(svgPath, pngPath) {
  const dir = dirname(svgPath);
  run("qlmanage", ["-t", "-s", "1920", "-o", dir, svgPath]);
  const produced = `${svgPath}.png`;
  if (!existsSync(produced)) {
    throw new Error(`qlmanage did not write ${produced}`);
  }
  run("ffmpeg", [
    "-y",
    "-i",
    produced,
    "-vf",
    `scale=${W}:${H}:force_original_aspect_ratio=increase:flags=lanczos,crop=${W}:${H},format=rgb24`,
    pngPath,
  ]);
}

function pickEvents(events, from, to, want) {
  const slice = events.filter((row) => row.seq >= from && row.seq <= to && row.text);
  if (slice.length === 0) return events.filter((row) => row.seq >= from && row.seq <= to);
  if (slice.length <= want) return slice;
  const out = [];
  for (let i = 0; i < want; i += 1) {
    const idx = Math.round((i * (slice.length - 1)) / (want - 1));
    const row = slice[idx];
    if (row && out[out.length - 1]?.seq !== row.seq) out.push(row);
  }
  return out;
}

function foldPanes(events, roster, featured, upto) {
  const byId = new Map(roster.map((bot) => [bot.id, bot]));
  const bySlug = new Map(roster.map((bot) => [bot.slug, bot]));
  const open = new Map();
  let last;
  for (const event of events) {
    if (event.seq > upto) break;
    const bot = (event.to && (byId.get(event.to) || bySlug.get(event.to))) || (event.slug && bySlug.get(event.slug));
    if (!bot) continue;
    last = { bot, event };
    if (event.type === "send.accepted" || event.type === "turn.start") {
      open.set(bot.id, {
        name: bot.name,
        slug: bot.slug,
        activity: "Running",
        text: String(event.text || bot.purpose || "").slice(0, 360),
      });
    } else if (event.type === "tool.call" || event.type === "tool.result" || event.type === "operator.message") {
      const prev = open.get(bot.id) || {
        name: bot.name,
        slug: bot.slug,
        activity: "Running",
        text: "",
      };
      const tool = event.type === "tool.call" ? String(event.text || "").split(/\s+/)[0] : prev.activity;
      open.set(bot.id, { ...prev, activity: tool, text: String(event.text || prev.text).slice(0, 360) });
    } else if (event.type === "turn.end") {
      open.delete(bot.id);
    }
  }
  let panes = [...open.values()];
  if (featured.length > 0) {
    const keys = new Set(featured.map((item) => item.toLowerCase()));
    const hit = panes.filter((pane) => keys.has(pane.slug.toLowerCase()));
    if (hit.length > 0) panes = hit;
  }
  if (panes.length === 0 && last) {
    panes = [
      {
        name: last.bot.name,
        slug: last.bot.slug,
        activity: last.event.type,
        text: String(last.event.text || "").slice(0, 360),
      },
    ];
  }
  return panes.slice(0, 4);
}

function concatPngs(dir, outMp4) {
  const files = readdirSync(dir)
    .filter((name) => /^\d{3}\.png$/.test(name))
    .sort();
  if (files.length === 0) throw new Error("no png frames");
  const lines = [];
  for (const name of files) {
    lines.push(`file '${join(dir, name)}'`);
    lines.push("duration 1.4");
  }
  lines.push(`file '${join(dir, files[files.length - 1])}'`);
  const listPath = join(dir, "concat.txt");
  writeFileSync(listPath, `${lines.join("\n")}\n`, "utf8");
  run("ffmpeg", [
    "-y",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    listPath,
    "-vf",
    `fps=30,scale=${W}:${H}:flags=lanczos,format=yuv420p`,
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-crf",
    "18",
    "-preset",
    "medium",
    "-movflags",
    "+faststart",
    outMp4,
  ]);
}

function posterFrom(mp4, jpg) {
  run("ffmpeg", ["-y", "-ss", "2.2", "-i", mp4, "-frames:v", "1", "-q:v", "3", jpg]);
}

function durationOf(mp4) {
  const probe = spawnSync(
    "ffprobe",
    ["-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", mp4],
    { encoding: "utf8" },
  );
  const sec = Number.parseFloat((probe.stdout || "").trim());
  if (!Number.isFinite(sec)) return "0:14";
  const whole = Math.max(1, Math.round(sec));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

const events = readJsonl(PROTOCOL);
const scenes = JSON.parse(readFileSync(SCENES, "utf8")).scenes ?? [];
const roster = JSON.parse(readFileSync(ROSTER, "utf8")).bots ?? [];
ensure(OUT);

const durations = {};
for (const cut of CUTS) {
  const scene = scenes.find((row) => row.id === cut.scene) ?? {
    seqFrom: 1,
    seqTo: events.at(-1)?.seq ?? 1,
    featured: [],
  };
  const work = join(tmpdir(), `maximor-film-${cut.id}`);
  rmSync(work, { recursive: true, force: true });
  ensure(work);
  const frames = [{ name: "000", svg: titleSvg(cut.title, cut.subtitle) }];
  const beats = pickEvents(events, scene.seqFrom || 1, scene.seqTo || 1, cut.id === "agent-memory" ? 10 : 8);
  beats.forEach((beat, index) => {
    const panes = foldPanes(events, roster, scene.featured ?? [], beat.seq);
    frames.push({
      name: String(index + 1).padStart(3, "0"),
      svg: frameSvg({
        title: cut.title,
        kicker: `SEQ ${beat.seq}  ·  ${String(beat.type).toUpperCase()}`,
        caption: String(beat.text || cut.subtitle).replace(/\s+/g, " ").slice(0, 160),
        panes,
      }),
    });
  });
  for (const frame of frames) {
    const svgPath = join(work, `${frame.name}.svg`);
    writeFileSync(svgPath, frame.svg, "utf8");
    raster(svgPath, join(work, `${frame.name}.png`));
  }
  const mp4 = join(OUT, `${cut.id}.mp4`);
  concatPngs(work, mp4);
  const jpg = join(OUT, `${cut.id}.jpg`);
  posterFrom(mp4, jpg);
  durations[cut.id] = durationOf(mp4);
  process.stdout.write(`${cut.id} ${durations[cut.id]}\n`);
}

writeFileSync(join(OUT, "durations.json"), `${JSON.stringify(durations, null, 2)}\n`, "utf8");
process.stdout.write(`wrote ${CUTS.length} films to ${OUT}\n`);
