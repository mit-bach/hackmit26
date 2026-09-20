#!/usr/bin/env node
/**
 * Cut 1920×1080 H.264 films from golden-20260920-r1 protocol.jsonl.
 * Cinema stills (HTML → Chrome screenshot) with an ffmpeg title-card fallback.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../..");
const GOLDEN = join(ROOT, ".cfo-v2/office/instances/golden-20260920-r1");
const PROTOCOL = join(GOLDEN, "harness/protocol.jsonl");
const SCENES = join(GOLDEN, "harness/demo/latest/scenes.json");
const ROSTER = join(GOLDEN, "harness/roster.json");
const OUT = join(ROOT, "web/public/videos");
const WIDTH = 1920;
const HEIGHT = 1080;

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
    subtitle: "memory_read / memory_write. Same method. Not last month’s number.",
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

const COLORS = ["#2dd4bf", "#60a5fa", "#c084fc", "#f472b6", "#fb923c", "#22d3ee", "#4ade80", "#f87171"];

function ensure(dir) {
  mkdirSync(dir, { recursive: true });
}

function readJsonl(path) {
  if (!existsSync(path)) return [];
  return readFileSync(path, "utf8")
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function layout(count) {
  if (count <= 1) return [{ left: 0, top: 0, width: 100, height: 100 }];
  if (count === 2) {
    return [
      { left: 0, top: 0, width: 50, height: 100 },
      { left: 50, top: 0, width: 50, height: 100 },
    ];
  }
  if (count === 3) {
    return [
      { left: 0, top: 0, width: 50, height: 100 },
      { left: 50, top: 0, width: 50, height: 50 },
      { left: 50, top: 50, width: 50, height: 50 },
    ];
  }
  const cols = count <= 4 ? 2 : 3;
  const rows = Math.ceil(count / cols);
  const cells = [];
  for (let i = 0; i < count; i += 1) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    cells.push({
      left: (col * 100) / cols,
      top: (row * 100) / rows,
      width: 100 / cols,
      height: 100 / rows,
    });
  }
  return cells;
}

function chromeBin() {
  const mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (existsSync(mac)) return mac;
  const which = spawnSync("which", ["google-chrome", "chromium", "chrome"], { encoding: "utf8" });
  const hit = (which.stdout || "").trim().split("\n")[0];
  return hit || "";
}

function ffmpeg(...args) {
  const result = spawnSync("ffmpeg", ["-y", ...args], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(result.stderr.slice(-800) || "ffmpeg failed");
  }
}

function frameHtml({ title, kicker, caption, panes }) {
  const cells = layout(Math.max(1, panes.length));
  const paneMarkup =
    panes.length === 0
      ? `<div class="empty">Wipe. No Bots are awake.</div>`
      : panes
          .map((pane, index) => {
            const cell = cells[index] ?? cells[0];
            const color = COLORS[index % COLORS.length];
            return `<section class="pane" style="left:${cell.left}%;top:${cell.top}%;width:${cell.width}%;height:${cell.height}%">
  <header>
    <span class="dot" style="background:${color}"></span>
    <div>
      <div class="name">${escapeHtml(pane.name)}</div>
      <div class="purpose">${escapeHtml(pane.purpose)}</div>
    </div>
    <span class="chip">${escapeHtml(pane.activity)}</span>
  </header>
  <pre>${escapeHtml(pane.text)}</pre>
</section>`;
          })
          .join("\n");
  return `<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html, body { margin: 0; width: ${WIDTH}px; height: ${HEIGHT}px; overflow: hidden; background: #07090c; color: #e8edf2; font-family: ui-sans-serif, "SF Pro Text", system-ui, sans-serif; }
  .stage { position: relative; width: ${WIDTH}px; height: ${HEIGHT}px; background: radial-gradient(1200px 700px at 50% -10%, #15202b 0%, #07090c 55%); }
  .pane { position: absolute; box-sizing: border-box; padding: 10px; }
  .pane header, .pane { pointer-events: none; }
  .pane > header { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border: 1px solid rgba(255,255,255,0.08); border-bottom: 0; border-radius: 16px 16px 0 0; background: #10141a; }
  .pane pre { margin: 0; height: calc(100% - 64px); overflow: hidden; padding: 18px 20px 72px; border: 1px solid rgba(255,255,255,0.08); border-radius: 0 0 16px 16px; background: #0c1016; font: 22px/1.45 ui-sans-serif, system-ui, sans-serif; white-space: pre-wrap; }
  .dot { width: 14px; height: 14px; border-radius: 99px; flex: none; }
  .name { font-size: 22px; font-weight: 650; }
  .purpose { font-size: 13px; color: #8b95a1; }
  .chip { margin-left: auto; border-radius: 999px; padding: 4px 12px; font-size: 13px; background: rgba(45,212,191,0.16); color: #5eead4; }
  .card { position: absolute; left: 0; right: 0; bottom: 0; padding: 48px 56px 40px; background: linear-gradient(to top, rgba(7,9,12,0.94), rgba(7,9,12,0.2) 70%, transparent); }
  .kicker { letter-spacing: 0.22em; text-transform: uppercase; color: #c9a24a; font-size: 14px; }
  .title { font-size: 42px; font-weight: 650; margin-top: 6px; }
  .caption { margin-top: 10px; font-size: 20px; color: #b7c0ca; max-width: 1400px; }
  .empty { position: absolute; inset: 0; display: grid; place-items: center; color: #8b95a1; font-size: 28px; }
</style>
</head>
<body>
  <div class="stage">
    ${paneMarkup}
    <div class="card">
      <div class="kicker">${escapeHtml(kicker)}</div>
      <div class="title">${escapeHtml(title)}</div>
      <div class="caption">${escapeHtml(caption)}</div>
    </div>
  </div>
</body>
</html>`;
}

function titleHtml(title, subtitle) {
  return `<!doctype html>
<html><head><meta charset="utf-8"/><style>
html,body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;background:#07090c;color:#e8edf2;font-family:ui-sans-serif,system-ui,sans-serif}
.wrap{width:${WIDTH}px;height:${HEIGHT}px;display:flex;flex-direction:column;justify-content:flex-end;padding:0 72px 88px;box-sizing:border-box;background:radial-gradient(900px 500px at 20% 20%, #1a2430, #07090c 60%)}
.k{letter-spacing:.28em;text-transform:uppercase;color:#c9a24a;font-size:16px}
h1{font-size:72px;margin:12px 0 18px;font-weight:650}
p{font-size:28px;color:#b7c0ca;max-width:1400px;margin:0}
</style></head>
<body><div class="wrap"><div class="k">Maximor · Golden desk</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(subtitle)}</p></div></body></html>`;
}

function screenshot(htmlPath, pngPath, chrome) {
  const args = [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-sandbox",
    `--window-size=${WIDTH},${HEIGHT}`,
    `--screenshot=${pngPath}`,
    `file://${htmlPath}`,
  ];
  const result = spawnSync(chrome, args, { encoding: "utf8", timeout: 20000 });
  if (result.status !== 0 || !existsSync(pngPath)) {
    throw new Error(result.stderr?.slice(-400) || "chrome screenshot failed");
  }
}

function pickEvents(events, from, to, want) {
  const slice = events.filter((row) => row.seq >= from && row.seq <= to);
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
  for (const event of events) {
    if (event.seq > upto) break;
    const bot = (event.to && (byId.get(event.to) || bySlug.get(event.to))) || (event.slug && bySlug.get(event.slug));
    if (!bot) continue;
    if (event.type === "send.accepted" || event.type === "turn.start") {
      open.set(bot.id, {
        name: bot.name,
        purpose: bot.purpose,
        slug: bot.slug,
        activity: event.type === "tool.call" ? String(event.text || "").split(/\s+/)[0] : "Running",
        text: String(event.text || bot.purpose).slice(0, 420),
      });
    } else if (event.type === "tool.call" || event.type === "tool.result" || event.type === "operator.message") {
      const prev = open.get(bot.id) || {
        name: bot.name,
        purpose: bot.purpose,
        slug: bot.slug,
        activity: "Running",
        text: "",
      };
      const tool = event.type === "tool.call" ? String(event.text || "").split(/\s+/)[0] : prev.activity;
      open.set(bot.id, { ...prev, activity: tool, text: String(event.text || prev.text).slice(0, 420) });
    } else if (event.type === "turn.end") {
      open.delete(bot.id);
    }
  }
  let panes = [...open.values()];
  if (featured.length > 0) {
    const keys = new Set(featured.map((item) => item.toLowerCase()));
    const hit = panes.filter((pane) => keys.has(pane.slug.toLowerCase()) || keys.has(pane.name.toLowerCase()));
    if (hit.length > 0) panes = hit;
  }
  if (panes.length === 0) {
    const last = [...events].reverse().find((event) => event.seq <= upto && (event.slug || event.to));
    if (last) {
      const bot = bySlug.get(last.slug) || byId.get(last.to) || { name: last.slug || last.to, purpose: "", slug: last.slug || "" };
      panes = [{ name: bot.name, purpose: bot.purpose || "", slug: bot.slug || "", activity: last.type, text: String(last.text || "").slice(0, 420) }];
    }
  }
  return panes.slice(0, 4);
}

function titleFallback(outMp4, title, subtitle, seconds) {
  const draw = [
    `drawtext=fontcolor=0xC9A24A:fontsize=36:x=72:y=h-220:text='Maximor · Golden desk'`,
    `drawtext=fontcolor=white:fontsize=64:x=72:y=h-160:text='${title.replaceAll("'", "’")}'`,
    `drawtext=fontcolor=0xB7C0CA:fontsize=28:x=72:y=h-80:text='${subtitle.replaceAll("'", "’")}'`,
  ].join(",");
  ffmpeg(
    "-f",
    "lavfi",
    "-i",
    `color=c=0x07090c:s=${WIDTH}x${HEIGHT}:d=${seconds}`,
    "-vf",
    draw,
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-crf",
    "18",
    "-preset",
    "slow",
    "-movflags",
    "+faststart",
    outMp4,
  );
}

function concatPngs(dir, outMp4, fps = 1) {
  const files = readdirSync(dir)
    .filter((name) => name.endsWith(".png"))
    .sort();
  if (files.length === 0) throw new Error("no png frames");
  const list = files.map((name) => `file '${join(dir, name)}'\nduration 1.35`).join("\n") + `\nfile '${join(dir, files[files.length - 1])}'\n`;
  const listPath = join(dir, "concat.txt");
  writeFileSync(listPath, list, "utf8");
  ffmpeg(
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    listPath,
    "-vf",
    `fps=30,scale=${WIDTH}:${HEIGHT}:flags=lanczos,format=yuv420p`,
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-crf",
    "18",
    "-preset",
    "slow",
    "-movflags",
    "+faststart",
    outMp4,
  );
}

function posterFrom(mp4, jpg) {
  ffmpeg("-ss", "2.4", "-i", mp4, "-frames:v", "1", "-q:v", "3", jpg);
}

function durationOf(mp4) {
  const probe = spawnSync(
    "ffprobe",
    ["-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", mp4],
    { encoding: "utf8" },
  );
  const sec = Number.parseFloat(probe.stdout.trim());
  if (!Number.isFinite(sec)) return "0:12";
  const whole = Math.max(1, Math.round(sec));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

const events = readJsonl(PROTOCOL);
const scenes = existsSync(SCENES) ? JSON.parse(readFileSync(SCENES, "utf8")).scenes ?? [] : [];
const roster = JSON.parse(readFileSync(ROSTER, "utf8")).bots ?? [];
const chrome = chromeBin();
ensure(OUT);

const durations = {};
for (const cut of CUTS) {
  const scene = scenes.find((row) => row.id === cut.scene) ?? { seqFrom: 1, seqTo: events.at(-1)?.seq ?? 1, featured: [] };
  const work = join(tmpdir(), `maximor-film-${cut.id}`);
  rmSync(work, { recursive: true, force: true });
  ensure(work);
  const mp4 = join(OUT, `${cut.id}.mp4`);
  try {
    if (!chrome) throw new Error("no chrome");
    writeFileSync(join(work, "title.html"), titleHtml(cut.title, cut.subtitle), "utf8");
    screenshot(join(work, "title.html"), join(work, "000.png"), chrome);
    const beats = pickEvents(events, scene.seqFrom || 1, scene.seqTo || events.at(-1)?.seq || 1, cut.id === "agent-memory" ? 12 : 9);
    beats.forEach((beat, index) => {
      const panes = foldPanes(events, roster, scene.featured ?? [], beat.seq);
      const html = frameHtml({
        title: cut.title,
        kicker: `seq ${beat.seq} · ${beat.type}`,
        caption: String(beat.text || cut.subtitle).replace(/\s+/g, " ").slice(0, 180),
        panes,
      });
      const htmlPath = join(work, `${String(index + 1).padStart(3, "0")}.html`);
      const pngPath = join(work, `${String(index + 1).padStart(3, "0")}.png`);
      writeFileSync(htmlPath, html, "utf8");
      screenshot(htmlPath, pngPath, chrome);
    });
    concatPngs(work, mp4);
  } catch (cause) {
    process.stderr.write(`${cut.id}: cinema stills failed (${cause instanceof Error ? cause.message : cause}); title card fallback\n`);
    titleFallback(mp4, cut.title, cut.subtitle, 12);
  }
  const jpg = join(OUT, `${cut.id}.jpg`);
  try {
    posterFrom(mp4, jpg);
  } catch {
    /* poster optional */
  }
  durations[cut.id] = durationOf(mp4);
  process.stdout.write(`${cut.id} ${durations[cut.id]} ${mp4}\n`);
}

writeFileSync(join(OUT, "durations.json"), JSON.stringify(durations, null, 2), "utf8");
process.stdout.write(`wrote ${CUTS.length} films to ${OUT}\n`);
