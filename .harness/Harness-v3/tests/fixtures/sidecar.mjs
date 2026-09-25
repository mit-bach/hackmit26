import http from "node:http";
import { writeFileSync } from "node:fs";

const portFile = process.env.SIDECAR_PORT_FILE;
if (!portFile) {
  process.stderr.write("SIDECAR_PORT_FILE required\n");
  process.exit(1);
}

const server = http.createServer((req, res) => {
  res.setHeader("content-type", "application/json");
  if (req.url === "/health") {
    res.end(JSON.stringify({ ok: true, result: { status: "ok" }, error: null }));
    return;
  }
  res.end(JSON.stringify({ ok: true, result: {}, error: null }));
});

server.listen(0, "127.0.0.1", () => {
  const addr = server.address();
  const port = typeof addr === "object" && addr ? addr.port : 0;
  writeFileSync(portFile, `${JSON.stringify({ host: "127.0.0.1", port })}\n`);
});
