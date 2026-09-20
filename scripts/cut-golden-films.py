#!/usr/bin/env python3
"""Render 1920x1080 Golden desk films with Pillow, then encode H.264."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / ".cfo-v2/office/instances/golden-20260920-r1"
PROTOCOL = GOLDEN / "harness/protocol.jsonl"
SCENES = GOLDEN / "harness/demo/latest/scenes.json"
ROSTER = GOLDEN / "harness/roster.json"
OUT = ROOT / "web/public/videos"
WORK = Path("/tmp/maximor-films")
W, H = 1920, 1080
BG = (7, 9, 12)
PANEL = (16, 20, 26)
INK = (232, 237, 242)
MUTED = (183, 192, 202)
BRASS = (201, 162, 74)
CHIP = (94, 234, 212)
CHIP_BG = (16, 52, 48)
COLORS = [
    (45, 212, 191),
    (96, 165, 250),
    (192, 132, 252),
    (244, 114, 182),
    (251, 146, 60),
    (34, 211, 238),
]
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

CUTS = [
    {
        "id": "invoice-to-close",
        "scene": "C",
        "title": "INV-001 reaches control",
        "subtitle": "AP prepares. ctl-pay concurs. AP does not pay.",
        "beats": 8,
    },
    {
        "id": "stripe-reconciliation",
        "scene": "stripe",
        "title": "Stripe payout unpack",
        "subtitle": "Charges, refunds, and fees on the tape. Not a closed bank match.",
        "beats": 8,
    },
    {
        "id": "month-end-across-periods",
        "scene": "M",
        "title": "Harbor Electric, two periods",
        "subtitle": "August $7,800 method recalled. September $4,650. Lock still BLOCKED.",
        "beats": 8,
    },
    {
        "id": "agent-memory",
        "scene": "M",
        "title": "September reads August",
        "subtitle": "memory_read / memory_write. Same method. Not last month's number.",
        "beats": 10,
    },
    {
        "id": "bad-invoice",
        "scene": "B",
        "title": "Inbox traps stay off the books",
        "subtitle": "Quote, statement, and newsletter never become payables.",
        "beats": 8,
    },
    {
        "id": "control-escalation",
        "scene": "E",
        "title": "$12.40 stays unexplained",
        "subtitle": "Cash HUMAN_REVIEW. ctl-cash. The month does not close.",
        "beats": 8,
    },
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and Path(FONT_BOLD).exists() else FONT
    return ImageFont.truetype(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, max_width: int, limit: int) -> list[str]:
    words = " ".join(str(text or "").split()).split(" ")
    lines: list[str] = []
    row = ""
    for word in words:
        trial = f"{row} {word}".strip()
        if draw.textlength(trial, font=face) <= max_width or not row:
            row = trial
        else:
            lines.append(row)
            row = word
        if len(lines) >= limit:
            return lines
    if row and len(lines) < limit:
        lines.append(row)
    return lines


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def layout(count: int) -> list[tuple[int, int, int, int]]:
    if count <= 1:
        return [(48, 40, W - 96, 740)]
    if count == 2:
        return [(48, 40, 900, 740), (972, 40, 900, 740)]
    if count == 3:
        return [(48, 40, 900, 740), (972, 40, 900, 356), (972, 424, 900, 356)]
    return [(48, 40, 900, 356), (972, 40, 900, 356), (48, 424, 900, 356), (972, 424, 900, 356)]


def paint_title(title: str, subtitle: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.ellipse((-80, -200, 720, 620), fill=(22, 30, 40))
    draw.text((72, 792), "MAXIMOR  ·  GOLDEN DESK", font=font(22, True), fill=BRASS)
    draw.text((72, 848), title, font=font(58, True), fill=INK)
    for i, line in enumerate(wrap(draw, subtitle, font(28), 1600, 2)):
        draw.text((72, 940 + i * 40), line, font=font(28), fill=MUTED)
    return img


def paint_frame(title: str, kicker: str, caption: str, panes: list[dict]) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    cells = layout(max(1, len(panes)))
    body = font(22)
    name_font = font(26, True)
    chip_font = font(16, True)
    for index, pane in enumerate(panes):
        x, y, w, h = cells[index]
        color = COLORS[index % len(COLORS)]
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL)
        draw.ellipse((x + 20, y + 22, x + 34, y + 36), fill=color)
        draw.text((x + 46, y + 16), pane["name"], font=name_font, fill=INK)
        chip = pane["activity"][:22]
        tw = draw.textlength(chip, font=chip_font)
        cx = x + w - 28 - tw
        draw.rounded_rectangle((cx - 14, y + 16, x + w - 16, y + 46), radius=14, fill=CHIP_BG)
        draw.text((cx, y + 21), chip, font=chip_font, fill=CHIP)
        lines = wrap(draw, pane["text"], body, w - 48, 12 if len(panes) <= 2 else 7)
        for line_i, line in enumerate(lines):
            draw.text((x + 24, y + 72 + line_i * 30), line, font=body, fill=(213, 221, 230))
    draw.rectangle((0, 800, W, H), fill=BG)
    draw.text((72, 848), kicker, font=font(18, True), fill=BRASS)
    draw.text((72, 888), title, font=font(40, True), fill=INK)
    cap_lines = wrap(draw, caption, font(22), 1700, 2)
    for i, line in enumerate(cap_lines):
        draw.text((72, 948 + i * 30), line, font=font(22), fill=MUTED)
    return img


def pick_events(events: list[dict], start: int, end: int, want: int) -> list[dict]:
    slice_ = [row for row in events if start <= row.get("seq", 0) <= end and row.get("text")]
    if not slice_:
        slice_ = [row for row in events if start <= row.get("seq", 0) <= end]
    if len(slice_) <= want:
        return slice_
    out = []
    for i in range(want):
        idx = round(i * (len(slice_) - 1) / (want - 1))
        row = slice_[idx]
        if not out or out[-1]["seq"] != row["seq"]:
            out.append(row)
    return out


def fold_panes(events: list[dict], roster: list[dict], featured: list[str], upto: int) -> list[dict]:
    by_id = {bot["id"]: bot for bot in roster}
    by_slug = {bot["slug"]: bot for bot in roster}
    open_panes: dict[str, dict] = {}
    last = None
    for event in events:
        if event.get("seq", 0) > upto:
            break
        bot = by_id.get(event.get("to") or "") or by_slug.get(event.get("to") or "") or by_slug.get(event.get("slug") or "")
        if not bot:
            continue
        last = (bot, event)
        kind = event.get("type")
        if kind in {"send.accepted", "turn.start"}:
            open_panes[bot["id"]] = {
                "name": bot["name"],
                "slug": bot["slug"],
                "activity": "Running",
                "text": str(event.get("text") or bot.get("purpose") or "")[:420],
            }
        elif kind in {"tool.call", "tool.result", "operator.message"}:
            prev = open_panes.get(bot["id"], {"name": bot["name"], "slug": bot["slug"], "activity": "Running", "text": ""})
            tool = str(event.get("text") or "").split()[0] if kind == "tool.call" else prev["activity"]
            open_panes[bot["id"]] = {
                **prev,
                "activity": tool,
                "text": str(event.get("text") or prev["text"])[:420],
            }
        elif kind == "turn.end":
            open_panes.pop(bot["id"], None)
    panes = list(open_panes.values())
    if featured:
        keys = {item.lower() for item in featured}
        hit = [pane for pane in panes if pane["slug"].lower() in keys]
        if hit:
            panes = hit
    if not panes and last:
        bot, event = last
        panes = [
            {
                "name": bot["name"],
                "slug": bot["slug"],
                "activity": str(event.get("type") or ""),
                "text": str(event.get("text") or "")[:420],
            }
        ]
    return panes[:4]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def encode(dir_path: Path, mp4: Path) -> None:
    files = sorted(dir_path.glob("*.png"))
    if not files:
        raise RuntimeError(f"no frames in {dir_path}")
    listing = dir_path / "concat.txt"
    lines = []
    for path in files:
        lines.append(f"file '{path}'")
        lines.append("duration 1.4")
    lines.append(f"file '{files[-1]}'")
    listing.write_text("\n".join(lines) + "\n")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-vf",
            "fps=30,format=yuv420p",
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
            str(mp4),
        ]
    )


def duration_of(mp4: Path) -> str:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(mp4)],
        check=True,
        capture_output=True,
        text=True,
    )
    sec = max(1, round(float(probe.stdout.strip())))
    return f"{sec // 60}:{sec % 60:02d}"


def main() -> None:
    events = read_jsonl(PROTOCOL)
    scenes = {row["id"]: row for row in json.loads(SCENES.read_text()).get("scenes", [])}
    roster = json.loads(ROSTER.read_text()).get("bots", [])
    OUT.mkdir(parents=True, exist_ok=True)
    if WORK.exists():
        shutil.rmtree(WORK)
    durations = {}
    for cut in CUTS:
        scene = scenes.get(cut["scene"], {"seqFrom": 1, "seqTo": events[-1]["seq"], "featured": []})
        dest = WORK / cut["id"]
        dest.mkdir(parents=True)
        frames = [paint_title(cut["title"], cut["subtitle"])]
        for beat in pick_events(events, scene.get("seqFrom", 1), scene.get("seqTo", 1), cut["beats"]):
            panes = fold_panes(events, roster, scene.get("featured", []), beat["seq"])
            frames.append(
                paint_frame(
                    cut["title"],
                    f"SEQ {beat['seq']}  ·  {str(beat.get('type') or '').upper()}",
                    " ".join(str(beat.get("text") or cut["subtitle"]).split())[:170],
                    panes,
                )
            )
        for index, image in enumerate(frames):
            image.save(dest / f"{index:03d}.png", "PNG")
        mp4 = OUT / f"{cut['id']}.mp4"
        encode(dest, mp4)
        run(["ffmpeg", "-y", "-ss", "2.4", "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(OUT / f"{cut['id']}.jpg")])
        durations[cut["id"]] = duration_of(mp4)
        print(f"{cut['id']} {durations[cut['id']]}")
    (OUT / "durations.json").write_text(json.dumps(durations, indent=2) + "\n")
    print(f"wrote {len(CUTS)} films to {OUT}")


if __name__ == "__main__":
    main()
