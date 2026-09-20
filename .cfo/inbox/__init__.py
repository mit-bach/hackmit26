"""Internal Gmail-like finance inbox: two-agent handoff into canonical AP."""

__all__ = ["handoff", "handoff_reply", "process_message", "receive_raw"]


def __getattr__(name: str):
    if name in __all__:
        from inbox import workflow

        return getattr(workflow, name)
    raise AttributeError(name)
