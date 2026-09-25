"""Loopback HTTP JSON, or newline JSON on stdio. One protocol."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from cfo_kernel.paths import Computer, attach_computer, current
from cfo_kernel.rpc import handle_rpc


def create_app(computer: Path | Computer | None = None) -> FastAPI:
    if computer is not None:
        root = computer.root if isinstance(computer, Computer) else Path(computer)
        attach_computer(root)
    app = FastAPI(title="cfo_kernel", docs_url=None, redoc_url=None)

    @app.get("/health")
    def health() -> dict:
        return handle_rpc(
            {
                "op": "kernel.health",
                "args": {},
                "botId": "kernel-host",
                "slug": "_host",
                "profile": "sidecar",
                "handleId": "",
                "idempotencyKey": None,
            }
        )

    @app.post("/rpc")
    def rpc(payload: dict) -> JSONResponse:
        return JSONResponse(handle_rpc(payload, computer=current()))

    return app


def run_stdio(computer: Computer | None = None) -> None:
    bound = computer or current()
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "result": None,
                        "error": {"code": "invalid_args", "message": str(exc)},
                        "traceId": "k_stdio",
                    }
                )
                + "\n"
            )
            sys.stdout.flush()
            continue
        if not isinstance(payload, dict):
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "result": None,
                        "error": {
                            "code": "invalid_args",
                            "message": "RPC line must be a JSON object",
                        },
                        "traceId": "k_stdio",
                    }
                )
                + "\n"
            )
            sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps(handle_rpc(payload, computer=bound), default=str) + "\n")
        sys.stdout.flush()


def run_http(host: str, port: int, computer: Computer | None = None) -> None:
    import threading
    import time
    import uvicorn

    bound = computer or current()
    app = create_app(bound)
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    def _publish_port() -> None:
        while not server.started:
            time.sleep(0.02)
        bound_port = port
        for http_server in server.servers:
            for sock in http_server.sockets:
                bound_port = sock.getsockname()[1]
        bound.port_path.write_text(
            json.dumps({"host": host, "port": bound_port}) + "\n"
        )

    threading.Thread(target=_publish_port, daemon=True).start()
    server.run()
