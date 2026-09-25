"""Queue owners for fail-closed Kernel statuses named HUMAN_REVIEW.

The status string stays. The owner is a Verifier Bot, never the Harness Operator.
"""

from __future__ import annotations

from typing import TypedDict


class QueueOwner(TypedDict):
    owner: str
    profile: str


# Kernel status HUMAN_REVIEW remains fail-closed. This map is the queue owner.
QUEUE_OWNERS: dict[tuple[str, str], QueueOwner] = {
    ("ap", "APPROVE"): {"owner": "ctl-pay", "profile": "review-match"},
    ("ap", "HUMAN_REVIEW"): {"owner": "ctl-pay", "profile": "review-match"},
    ("pay", "RELEASE"): {"owner": "ctl-pay", "profile": "review-pay"},
    ("collect", "WRITE_OFF"): {"owner": "ctl-pay", "profile": "review-pay"},
    ("apply", "HUMAN_REVIEW"): {"owner": "ctl-cash", "profile": "review-apply"},
    ("ar", "HUMAN_REVIEW"): {"owner": "ctl-cash", "profile": "review-apply"},
    ("cash", "HUMAN_REVIEW"): {"owner": "ctl-cash", "profile": "review-rec"},
    ("cash_recon", "HUMAN_REVIEW"): {"owner": "ctl-cash", "profile": "review-rec"},
    ("cash_recon", "UNEXPLAINED_DIFFERENCE"): {"owner": "ctl-cash", "profile": "review-rec"},
    ("close", "TREATMENT"): {"owner": "ctl-books", "profile": "review-treatment"},
    ("close", "LOCK"): {"owner": "ctl-books", "profile": "lock"},
    ("close", "HUMAN_REVIEW"): {"owner": "ctl-books", "profile": "lock"},
}

CLOSE_WORKFLOW_OWNERS: dict[str, QueueOwner] = {
    "cash": {"owner": "ctl-cash", "profile": "review-rec"},
    "ar": {"owner": "ctl-cash", "profile": "review-apply"},
    "prepaid": {"owner": "ctl-books", "profile": "review-treatment"},
    "depreciation": {"owner": "ctl-books", "profile": "review-treatment"},
    "bs_recon": {"owner": "ctl-books", "profile": "review-treatment"},
    "exceptions": {"owner": "ctl-books", "profile": "lock"},
    "final_review": {"owner": "ctl-books", "profile": "lock"},
    "mark_closed": {"owner": "ctl-books", "profile": "lock"},
}

VERIFIER_SLUGS = frozenset({"ctl-pay", "ctl-cash", "ctl-books"})


def owner_for(pipe: str, status: str) -> QueueOwner:
    key = (pipe, status)
    if key in QUEUE_OWNERS:
        return QUEUE_OWNERS[key]
    if pipe in {"apply", "ar"}:
        return {"owner": "ctl-cash", "profile": "review-apply"}
    if pipe in {"cash", "cash_recon"}:
        return {"owner": "ctl-cash", "profile": "review-rec"}
    if pipe in {"ap", "pay", "collect"}:
        return {"owner": "ctl-pay", "profile": "review-match" if pipe == "ap" else "review-pay"}
    return {"owner": "ctl-books", "profile": "lock"}


def owner_for_close_workflow(source_workflow: str) -> QueueOwner:
    return CLOSE_WORKFLOW_OWNERS.get(
        source_workflow, {"owner": "ctl-books", "profile": "review-treatment"}
    )


def payload_for(pipe: str, status: str) -> dict[str, object]:
    owner = owner_for(pipe, status)
    return {
        "owner": owner["owner"],
        "profile": owner["profile"],
        "kernelStatus": status,
        "humanQueue": False,
    }
