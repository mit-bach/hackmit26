import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative, resolve, sep } from "node:path";
import type { IncomingMessage, ServerResponse } from "node:http";

import { harnessPackageRoot } from "../pkg.ts";

const MIME: Readonly<Record<string, string>> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".json": "application/json; charset=utf-8",
  ".woff2": "font/woff2",
  ".map": "application/json; charset=utf-8",
};

export function uiDistDir(): string {
  return join(harnessPackageRoot(), "ui", "dist");
}

export function tryServeStatic(req: IncomingMessage, res: ServerResponse): boolean {
  if ((req.method ?? "GET") !== "GET") {
    return false;
  }
  const urlPath = new URL(req.url ?? "/", "http://127.0.0.1").pathname;
  if (urlPath.startsWith("/v1/") || urlPath.startsWith("/api/") || urlPath === "/health") {
    return false;
  }
  const root = resolve(uiDistDir());
  if (!existsSync(root)) {
    return false;
  }
  const cleaned = decodeURIComponent(urlPath.split("?")[0] ?? "/");
  const rel = cleaned === "/" ? "index.html" : cleaned.replace(/^\/+/, "");
  if (rel.includes("..") || rel.includes("\0")) {
    return false;
  }
  let file = resolve(root, rel);
  const relToRoot = relative(root, file);
  if (relToRoot.startsWith("..") || relToRoot.includes(`..${sep}`)) {
    return false;
  }
  if (!existsSync(file) || statSync(file).isDirectory()) {
    file = join(root, "index.html");
  }
  if (!existsSync(file)) {
    return false;
  }
  const data = readFileSync(file);
  res.writeHead(200, {
    "content-type": MIME[extname(file)] ?? "application/octet-stream",
    "cache-control": urlPath === "/" || extname(file) === ".html" ? "no-store" : "public, max-age=60",
  });
  res.end(data);
  return true;
}
