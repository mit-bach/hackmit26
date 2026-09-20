"""Launch the Maximor demo website API."""

from __future__ import annotations

import argparse

from demo_web.app import create_app
from demo_web.workspace import CANONICAL, DEFAULT_RUNTIME


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Maximor Office of the CFO demo website")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--canonical", default=str(CANONICAL))
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    args = parser.parse_args(argv)

    import uvicorn

    from pathlib import Path

    app = create_app(Path(args.canonical), Path(args.runtime))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
