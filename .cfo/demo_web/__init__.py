"""Thin FastAPI façade over the existing Maximor Office of the CFO."""

from demo_web.app import create_app

__all__ = ["create_app"]
